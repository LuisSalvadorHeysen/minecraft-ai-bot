#!/usr/bin/env python3
"""
MCP Tool Executor
Converts complex instructions into MCP tool calls and executes them via the MCP server
"""

import os
import json
import subprocess
import sys
import signal
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

BASE_URL = "https://pygmalion.herdora.com/v1"

# Initialize Herdora client
client = OpenAI(
    #base_url=BASE_URL,
    #api_key=os.environ.get("HERDORA_API_KEY"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MCP_TOOL_PROMPT = """You are controlling a Minecraft bot connected to an MCP server. Your goal is to **convert every complex instruction into a list of MCP tool calls**, then send them to the server. Follow these rules:

1. **Always respond with a JSON array of MCP tool calls**:
   Example:
   [
     {"tool": "send-chat", "args": {"message": "/tp @p 100 64 100"}},
     {"tool": "place-block", "args": {"x": 100, "y": 64, "z": 100}}
   ]

2. **Available MCP Tools**:

**Position and Movement:**
- {"tool": "get-position", "args": {}}
- {"tool": "move-to-position", "args": {"x": 100, "y": 64, "z": 100}}
- {"tool": "look-at", "args": {"x": 100, "y": 64, "z": 100}}
- {"tool": "jump", "args": {}}
- {"tool": "move-in-direction", "args": {"direction": "forward", "duration": 1000}}

**Flight:**
- {"tool": "fly-to", "args": {"x": 100, "y": 64, "z": 100}}

**Inventory:**
- {"tool": "list-inventory", "args": {}}
- {"tool": "find-item", "args": {"nameOrType": "diamond"}}
- {"tool": "equip-item", "args": {"itemName": "diamond"}}

**Block Interaction:**
- {"tool": "place-block", "args": {"x": 100, "y": 64, "z": 100}}
- {"tool": "dig-block", "args": {"x": 100, "y": 64, "z": 100}}
- {"tool": "get-block-info", "args": {"x": 100, "y": 64, "z": 100}}
- {"tool": "find-block", "args": {"blockType": "stone"}}

**Entity Interaction:**
- {"tool": "find-entity", "args": {"type": "player"}}

**Communication:**
- {"tool": "send-chat", "args": {"message": "/fill ~ ~ ~ ~5 ~5 ~5 stone"}}
- {"tool": "read-chat", "args": {"count": 10}}

**Game State:**
- {"tool": "detect-gamemode", "args": {}}

3. **IMPORTANT: Use MCP tools, NOT Minecraft commands directly.**
   - For chat messages: use "send-chat" tool with the message
   - For building: use "place-block" tool with coordinates
   - For movement: use "move-to-position" or "fly-to" tools
   - For inventory: use "list-inventory", "find-item", "equip-item" tools
   - For block operations: use "dig-block", "get-block-info", "find-block" tools

4. **For Minecraft commands** like /fill, /tp, /say, /gamemode, etc., use the "send-chat" tool.

5. **For bot-specific actions** like movement, inventory, block placement, use the appropriate MCP tools directly.

6. **Always base relative coordinates (`~`) on the bot's current position** - you may need to call "get-position" first.

7. **Handle multi-step instructions as a sequence of tool calls**.

Example instruction and response:

Instruction: "build a flat stone surface at my current position"  
Bot JSON output:
[
  {"tool": "get-position", "args": {}},
  {"tool": "send-chat", "args": {"message": "/fill ~-5 ~ ~-5 ~5 ~ ~5 stone"}}
]

Instruction: "send a message in chat saying hello"  
Bot JSON output:
[
  {"tool": "send-chat", "args": {"message": "/say hello"}}
]

Instruction: "place a stone block at my current position"  
Bot JSON output:
[
  {"tool": "get-position", "args": {}},
  {"tool": "place-block", "args": {"x": "~", "y": "~", "z": "~"}}
]

Instruction: "find diamonds and equip them"  
Bot JSON output:
[
  {"tool": "find-item", "args": {"nameOrType": "diamond"}},
  {"tool": "equip-item", "args": {"itemName": "diamond"}}
]

Now, convert every new instruction you receive into a **JSON array of MCP tool calls** following these rules.

Instruction: "{instruction}"

Respond ONLY with a JSON array of MCP tool calls."""

class MCPToolExecutor:
    def __init__(self):
        self.mcp_process = None
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully"""
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Clean up on Ctrl+C"""
        print("\nShutting down...")
        if self.mcp_process:
            self.mcp_process.terminate()
        sys.exit(0)
    
    def convert_instruction_to_tools(self, instruction: str) -> list:
        """Convert a high-level instruction into a list of MCP tool calls"""
        try:
            # Replace the placeholder in the prompt with the actual instruction
            prompt = MCP_TOOL_PROMPT.replace("{instruction}", instruction)
            
            response = client.chat.completions.create(
                model="Qwen/Qwen3-VL-235B-A22B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": f"Convert this instruction: {instruction}"}],
                    },
                ],
                max_tokens=512,
            )
            
            # Get the response content
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                tools = json.loads(content)
                if isinstance(tools, list):
                    return tools
                else:
                    print(f"Warning: Response is not a list: {tools}")
                    return [{"tool": "send-chat", "args": {"message": content}}]  # Fallback
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON response: {content}")
                return [{"tool": "send-chat", "args": {"message": content}}]  # Fallback
                
        except Exception as e:
            print(f"Error converting instruction: {e}")
            return None
    
    def start_mcp_server(self):
        """Start the MCP server as a subprocess"""
        try:
            # Prompt for port with default
            port_input = input("Enter port (default: 39613): ").strip()
            port = port_input if port_input else "39613"
            
            # Prompt for username with default
            username_input = input("Enter bot username (default: MyBot): ").strip()
            username = username_input if username_input else "MyBot"
            
            print(f"Starting MCP server on port {port} with username {username}...")
            
            self.mcp_process = subprocess.Popen(
                ["npx", "github:LuisSalvadorHeysen/minecraft-mcp-server#main", "--host", "localhost", "--port", port, "--username", username],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True
            )
            print("MCP server started")
            return self.mcp_process
        except FileNotFoundError:
            print("Warning: npx not found. Please install Node.js and npm.")
            return None
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            print("Assuming MCP server is already running.")
            return None
    
    def send_mcp_tool_call(self, tool_name: str, args: dict):
        """Send an MCP tool call to the server and return response"""
        mcp_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            }
        }
        
        json_message = json.dumps(mcp_message) + "\n"
        
        if self.mcp_process and self.mcp_process.stdin:
            try:
                # Send tool call
                self.mcp_process.stdin.write(json_message)
                self.mcp_process.stdin.flush()
                
                # Read response
                if self.mcp_process.stdout:
                    try:
                        response = self.mcp_process.stdout.readline()
                        if response:
                            try:
                                response_data = json.loads(response.strip())
                                if "result" in response_data:
                                    return response_data["result"].get("content", [{}])[0].get("text", "No response text")
                                elif "error" in response_data:
                                    return f"Error: {response_data['error'].get('message', 'Unknown error')}"
                            except json.JSONDecodeError:
                                return response.strip()
                        return "No response"
                    except:
                        return "Response read error"
                
                return "Tool call sent successfully"
            except Exception as e:
                return f"Error sending tool call: {e}"
        else:
            return "MCP server not available"
    
    def execute_instruction(self, instruction: str):
        """Convert instruction to MCP tool calls and execute them"""
        print(f"\nConverting instruction: '{instruction}'")
        
        # Convert instruction to tool calls
        tools = self.convert_instruction_to_tools(instruction)
        
        if not tools:
            print("Failed to convert instruction")
            return
        
        print(f"\nGenerated {len(tools)} MCP tool calls:")
        print(json.dumps(tools, indent=2))
        
        # Execute tool calls in sequence
        print(f"\nExecuting MCP tool calls...")
        for i, tool_call in enumerate(tools, 1):
            tool_name = tool_call.get("tool", "unknown")
            args = tool_call.get("args", {})
            
            print(f"\nExecuting tool call {i}/{len(tools)}: {tool_name}")
            print(f"Arguments: {json.dumps(args, indent=2)}")
            
            response = self.send_mcp_tool_call(tool_name, args)
            print(f"Server response: {response}")
        
        print(f"\nAll tool calls executed!")
    
    def run_interactive(self):
        """Run interactive mode"""
        print("MCP Tool Executor started")
        print("Converts complex instructions into MCP tool calls")
        print("(Press Ctrl+C to exit)")
        
        # Start MCP server
        self.start_mcp_server()
        
        while True:
            try:
                # Get user input
                instruction = input("\nEnter instruction: ").strip()
                
                if not instruction:
                    continue
                
                if instruction.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Execute the instruction
                self.execute_instruction(instruction)
                
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except EOFError:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Check if API key is configured
    if not os.environ.get("HERDORA_API_KEY"):
        print("Error: HERDORA_API_KEY not found in .env file")
        print("Please add your Herdora API key to the .env file:")
        print("HERDORA_API_KEY=your-herdora-api-key-here")
        sys.exit(1)
    
    executor = MCPToolExecutor()
    executor.run_interactive()
