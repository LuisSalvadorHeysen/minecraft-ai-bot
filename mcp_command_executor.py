#!/usr/bin/env python3
"""
MCP Command Executor
Converts complex instructions into JSON arrays of Minecraft commands and executes them via MCP server
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

MCP_COMMAND_PROMPT = """You are controlling a Minecraft bot connected to an MCP server. Your goal is to **convert every complex instruction into a list of executable Minecraft commands**, then send them to the server. Follow these rules:

1. **Always respond with a JSON array of commands**:
   Example:
   [
     "/tp 100 64 100",
     "/fill ~-5 ~ ~-5 ~5 ~ ~5 stone"
   ]

2. **For standard Minecraft commands** like /fill, /tp, /say, /gamemode, etc., **wrap them as chat messages** using the MCP server's send-chat interface.

3. **Movement and bot-specific commands** (like jump, move-in-direction, list-inventory) are sent using the native bot API.

4. **After sending each command**, print the server's response so the user can see what happened.

5. Only output the JSON array of commands. Do not add extra explanations.

6. Always base relative coordinates (`~`) on the bot's **current position**.

Example instruction and response:

Instruction: "build a flat stone surface at my current position"  
Bot JSON output:
[
  "/fill ~-5 ~ ~-5 ~5 ~ ~5 stone"
]

Instruction: "send a message in chat saying hello"  
Bot JSON output:
[
  "/say hello"
]

Now, convert every new instruction you receive into a **JSON array of commands** following these rules.

Instruction: "{instruction}"

Respond ONLY with a JSON array of commands."""

class MCPCommandExecutor:
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
    
    def convert_instruction_to_commands(self, instruction: str) -> list:
        """Convert a high-level instruction into a list of Minecraft commands"""
        try:
            # Replace the placeholder in the prompt with the actual instruction
            prompt = MCP_COMMAND_PROMPT.replace("{instruction}", instruction)
            
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
                commands = json.loads(content)
                if isinstance(commands, list):
                    return commands
                else:
                    print(f"Warning: Response is not a list: {commands}")
                    return [content]  # Fallback to single command
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON response: {content}")
                return [content]  # Fallback to single command
                
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
    
    def send_command_to_mcp(self, command):
        """Send a single command to MCP server and return response"""
        mcp_message = {
            "command": "chat",
            "args": {
                "message": command
            }
        }
        
        json_message = json.dumps(mcp_message) + "\n"
        
        if self.mcp_process and self.mcp_process.stdin:
            try:
                # Send command
                self.mcp_process.stdin.write(json_message)
                self.mcp_process.stdin.flush()
                
                # Read response
                if self.mcp_process.stdout:
                    try:
                        response = self.mcp_process.stdout.readline()
                        return response.strip() if response else "No response"
                    except:
                        return "Response read error"
                
                return "Command sent successfully"
            except Exception as e:
                return f"Error sending command: {e}"
        else:
            return "MCP server not available"
    
    def execute_instruction(self, instruction: str):
        """Convert instruction to commands and execute them"""
        print(f"\nConverting instruction: '{instruction}'")
        
        # Convert instruction to commands
        commands = self.convert_instruction_to_commands(instruction)
        
        if not commands:
            print("Failed to convert instruction")
            return
        
        print(f"\nGenerated {len(commands)} commands:")
        print(json.dumps(commands, indent=2))
        
        # Execute commands in sequence
        print(f"\nExecuting commands...")
        for i, cmd in enumerate(commands, 1):
            print(f"\nExecuting command {i}/{len(commands)}: {cmd}")
            response = self.send_command_to_mcp(cmd)
            print(f"Server response: {response}")
        
        print(f"\nAll commands executed!")
    
    def run_interactive(self):
        """Run interactive mode"""
        print("MCP Command Executor started")
        print("Converts complex instructions into executable Minecraft commands")
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
    
    executor = MCPCommandExecutor()
    executor.run_interactive()
