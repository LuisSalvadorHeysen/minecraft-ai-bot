#!/usr/bin/env python3
"""
Minecraft AI Controller
Controls the minecraft-mcp-server bot using OpenAI API
"""

import openai
import subprocess
import os
import json
import sys
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MinecraftController:
    def __init__(self):
        self.openai_client = None
        self.mcp_process = None
        self.setup_openai()
        self.setup_signal_handlers()
    
    def setup_openai(self):
        """Initialize OpenAI client with API key"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY not found in .env file")
            sys.exit(1)
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        print("OpenAI client initialized")
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully"""
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Clean up on Ctrl+C"""
        print("\nShutting down...")
        if self.mcp_process:
            self.mcp_process.terminate()
        sys.exit(0)
    
    def start_mcp_server(self):
        """Start the MCP server as a subprocess"""
        try:
            # Check if index.js exists in current directory
            if not os.path.exists('index.js'):
                print("Warning: index.js not found. Assuming MCP server is already running.")
                return None
            
            self.mcp_process = subprocess.Popen(
                ["node", "index.js", "--host", "localhost", "--port", "25565", "--username", "MyBot"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True
            )
            print("MCP server started")
            return self.mcp_process
        except FileNotFoundError:
            print("Warning: Node.js not found. Assuming MCP server is already running.")
            return None
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            print("Assuming MCP server is already running.")
            return None
    
    def get_minecraft_command(self, user_input):
        """Send user input to OpenAI and get Minecraft command"""
        system_prompt = """You are a Minecraft assistant.
You ONLY output valid Minecraft commands (nothing else).

Use vanilla commands like:
/tp <x> <y> <z>
/fill <x1> <y1> <z1> <x2> <y2> <z2> <block>
/clone <x1> <y1> <z1> <x2> <y2> <z2> <x> <y> <z>
/setblock <x> <y> <z> <block>
/give <player> <item> <count>

Rules:
- Do not explain the command.
- Do not include backticks or quotes.
- Output exactly ONE command per response."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            command = response.choices[0].message.content.strip()
            return command
        except Exception as e:
            print(f"Error getting command from OpenAI: {e}")
            return None
    
    def send_to_mcp(self, command):
        """Send command to MCP server"""
        mcp_message = {
            "command": "chat",
            "args": {
                "message": command
            }
        }
        
        json_message = json.dumps(mcp_message) + "\n"
        
        if self.mcp_process and self.mcp_process.stdin:
            try:
                self.mcp_process.stdin.write(json_message)
                self.mcp_process.stdin.flush()
                return True
            except Exception as e:
                print(f"Error sending to MCP server: {e}")
                return False
        else:
            print("MCP server not available. Command would be:")
            print(json_message.strip())
            return False
    
    def handle_error_retry(self, command, error_message):
        """Handle command errors by asking OpenAI for a corrected command"""
        retry_prompt = f"The command failed with error: {error_message}. Suggest a corrected command."
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Minecraft assistant. You ONLY output valid Minecraft commands (nothing else)."},
                    {"role": "user", "content": f"Original command: {command}"},
                    {"role": "user", "content": retry_prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            corrected_command = response.choices[0].message.content.strip()
            return corrected_command
        except Exception as e:
            print(f"Error getting corrected command: {e}")
            return None
    
    def run(self):
        """Main interactive loop"""
        print("Minecraft AI Controller started. Type instructions:")
        print("(Press Ctrl+C to exit)")
        
        # Start MCP server
        self.start_mcp_server()
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Get Minecraft command from OpenAI
                command = self.get_minecraft_command(user_input)
                
                if not command:
                    print("Failed to generate command")
                    continue
                
                print(f"Generated command: {command}")
                
                # Send to MCP server
                success = self.send_to_mcp(command)
                
                if success:
                    print("Command sent to MCP server")
                    
                    # Check for errors in MCP response (stretch goal)
                    if self.mcp_process and self.mcp_process.stdout:
                        try:
                            # Non-blocking read to check for immediate errors
                            import select
                            if select.select([self.mcp_process.stdout], [], [], 0.1)[0]:
                                response = self.mcp_process.stdout.readline()
                                if response and "error" in response.lower():
                                    print(f"MCP Error: {response.strip()}")
                                    corrected = self.handle_error_retry(command, response.strip())
                                    if corrected:
                                        print(f"Retrying with: {corrected}")
                                        self.send_to_mcp(corrected)
                        except:
                            pass  # Ignore errors in error checking
                
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except EOFError:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    controller = MinecraftController()
    controller.run()
