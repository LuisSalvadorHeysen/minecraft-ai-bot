#!/usr/bin/env python3
"""
MCP Construction Planner
Converts complex construction instructions into detailed step-by-step plans with multiple tool calls
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
    base_url=BASE_URL,
    api_key=os.environ.get("HERDORA_API_KEY"),
)

CONSTRUCTION_PLANNER_PROMPT = """You are controlling a Minecraft bot connected to an MCP server. For **every instruction**, no matter how complex:

1. **Always generate a complete sequence of tool calls** that fully executes the task.  
2. **Do not output the construction plan as text** or chat; it should only be executed via tool calls.  
3. **Standard Minecraft commands** (like /fill, /tp, /say, /gamemode, etc.) must be sent using the `send-chat` tool.  
4. **Complex instructions must be broken down into multiple steps**, including:  
   - Checking current position (`get-position`)  
   - Gathering or equipping materials (`find-item`, `equip-item`) if needed  
   - Moving to correct positions (`move-to-position`, `fly-to`)  
   - Placing blocks layer by layer (`place-block` or `/fill`)  
   - Any other required commands to complete the instruction  
5. **Always output a JSON array of tool calls**. No extra explanation or messages.  
6. **Every tool call is executed** immediately by the bot. There is no "plan only" step.  
7. **Keep responses concise** - use efficient /fill commands instead of many individual commands.

Example:

Instruction: "build an Egyptian pyramid at current position"

Output:
[
  { "tool": "get-position", "args": {} },
  { "tool": "send-chat", "args": { "message": "/fill ~-7 ~ ~-7 ~7 ~ ~7 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-6 ~1 ~-6 ~6 ~1 ~6 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-5 ~2 ~-5 ~5 ~2 ~5 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-4 ~3 ~-4 ~4 ~3 ~4 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-3 ~4 ~-3 ~3 ~4 ~3 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-2 ~5 ~-2 ~2 ~5 ~2 sandstone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~ ~6 ~ ~ ~6 ~ gold_block" } }
]

Instruction: "{instruction}"

Respond ONLY with a JSON array of tool calls."""

class MCPConstructionPlanner:
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
    
    def plan_construction(self, instruction: str) -> list:
        """Convert a complex construction instruction into a detailed step-by-step plan"""
        try:
            # Replace the placeholder in the prompt with the actual instruction
            prompt = CONSTRUCTION_PLANNER_PROMPT.replace("{instruction}", instruction)
            
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
                max_tokens=512,  # Reduced to prevent truncation
            )
            
            # Get the response content
            content = response.choices[0].message.content.strip()
            print(f"DEBUG: Raw AI response length: {len(content)}")
            
            # Try to parse as JSON
            try:
                plan = json.loads(content)
                if isinstance(plan, list):
                    print(f"DEBUG: Successfully parsed {len(plan)} tool calls")
                    return plan
                else:
                    print(f"Warning: Response is not a list: {plan}")
                    return [{"tool": "send-chat", "args": {"message": content}}]  # Fallback
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                
                # Try to extract JSON from the content if it's wrapped in text
                try:
                    # Look for JSON array in the content
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        print(f"DEBUG: Extracted JSON string length: {len(json_str)}")
                        plan = json.loads(json_str)
                        if isinstance(plan, list):
                            print(f"DEBUG: Successfully parsed {len(plan)} tool calls from extracted JSON")
                            return plan
                except Exception as extract_error:
                    print(f"DEBUG: JSON extraction failed: {extract_error}")
                
                # If JSON is truncated, try to fix it
                try:
                    # Find the last complete tool call
                    last_complete_idx = content.rfind('}')
                    if last_complete_idx != -1:
                        # Try to find the last complete array element
                        truncated_content = content[:last_complete_idx + 1]
                        # Add closing bracket if missing
                        if not truncated_content.endswith(']'):
                            truncated_content += ']'
                        print(f"DEBUG: Trying to fix truncated JSON: {truncated_content[-50:]}...")
                        plan = json.loads(truncated_content)
                        if isinstance(plan, list):
                            print(f"DEBUG: Successfully parsed {len(plan)} tool calls from truncated JSON")
                            return plan
                except Exception as fix_error:
                    print(f"DEBUG: JSON truncation fix failed: {fix_error}")
                
                return [{"tool": "send-chat", "args": {"message": content}}]  # Fallback
                
        except Exception as e:
            print(f"Error planning construction: {e}")
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
    
    def execute_construction_plan(self, instruction: str):
        """Convert instruction to construction plan and execute it step by step"""
        print(f"\nExecuting construction: '{instruction}'")
        
        # Convert instruction to construction plan
        plan = self.plan_construction(instruction)
        
        if not plan:
            print("Failed to create construction plan")
            return
        
        print(f"\nGenerated {len(plan)} tool calls - executing immediately...")
        
        # Execute plan step by step immediately
        for i, step in enumerate(plan, 1):
            tool_name = step.get("tool", "unknown")
            args = step.get("args", {})
            
            print(f"\nStep {i}/{len(plan)}: {tool_name}")
            if args:
                print(f"Args: {json.dumps(args, indent=2)}")
            
            response = self.send_mcp_tool_call(tool_name, args)
            print(f"Response: {response}")
            
            # Add a small delay between steps for better readability
            import time
            time.sleep(0.5)
        
        print(f"\nConstruction completed!")
    
    def run_interactive(self):
        """Run interactive construction planning mode"""
        print("MCP Construction Planner started")
        print("Converts complex construction instructions into immediate execution")
        print("(Press Ctrl+C to exit)")
        
        # Start MCP server
        self.start_mcp_server()
        
        while True:
            try:
                # Get user input
                instruction = input("\nEnter construction instruction: ").strip()
                
                if not instruction:
                    continue
                
                if instruction.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Execute the construction plan immediately
                self.execute_construction_plan(instruction)
                
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
    
    planner = MCPConstructionPlanner()
    planner.run_interactive()
