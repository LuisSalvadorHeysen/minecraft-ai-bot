#!/usr/bin/env python3
"""
Minecraft AI Controller using Herdora API
Controls the minecraft-mcp-server bot using Herdora's Qwen model
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

SYSTEM_PROMPT = """You are an AI that controls a Minecraft bot.
Always respond with valid Minecraft commands such as:
/tp, /fill, /clone, /setblock, /summon, /give, /say, etc.
Do not explain. Just output the command(s).
Use @p for the player when appropriate."""

class MinecraftBotAI:
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
    
    def ask_bot(self, user_message: str) -> str:
        """Send user message to Herdora and get Minecraft command"""
        try:
            response = client.chat.completions.create(
                model="Qwen/Qwen3-VL-235B-A22B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": SYSTEM_PROMPT,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_message}],
                    },
                ],
                max_tokens=128,
            )
            
            # Access response content directly as shown in the sample
            content = response.choices[0].message.content
            return content.strip()
                
        except Exception as e:
            print(f"Error getting command from Herdora API: {e}")
            return None
    
    def convert_instruction_to_commands(self, instruction: str) -> list:
        """Convert a high-level instruction into a list of Minecraft commands"""
        try:
            conversion_prompt = """You are controlling a Minecraft bot.  
Your task is to convert high-level instructions into a **list of valid Minecraft commands** that, if executed in order, will fulfill the instruction.  
 
- Only output a JSON array of strings.  
- Each string is a valid Minecraft command that can be sent directly to the server.  
- Do NOT write explanations or natural language.  
- Assume the bot is in Creative mode and has all necessary blocks.  
- Use absolute or relative coordinates as needed.  
- Example:
 
Instruction: "Build a T shape with grass blocks at the bot's current position"
 
JSON output:
[
  "/tp @p ~ ~ ~",
  "/fill ~-1 ~ ~-1 ~1 ~ ~1 grass_block"
]
 
Instruction: """ + instruction + """
 
Respond ONLY with a JSON array of Minecraft commands."""
            
            response = client.chat.completions.create(
                model="Qwen/Qwen3-VL-235B-A22B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": conversion_prompt,
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
    
    def run_interactive(self):
        """Run interactive mode"""
        print("Minecraft AI Bot (Herdora) started. Type instructions:")
        print("(Press Ctrl+C to exit)")
        
        # Start MCP server
        self.start_mcp_server()
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Get Minecraft command from Herdora
                command = self.ask_bot(user_input)
                
                if not command:
                    print("Failed to generate command")
                    continue
                
                print(f"AI Minecraft Command: {command}")
                
                # Send to MCP server
                success = self.send_to_mcp(command)
                
                if success:
                    print("Command sent to MCP server")
                
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except EOFError:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
    
    def test_command(self, test_message="Teleport me to 100 64 -200"):
        """Test the bot with a specific command"""
        print(f"Testing with: '{test_message}'")
        command = self.ask_bot(test_message)
        if command:
            print(f"AI Minecraft Command: {command}")
            return command
        else:
            print("Failed to generate test command")
            return None

# Standalone function for external use
def ask_bot(user_message: str) -> str:
    """Standalone function to ask the bot for a Minecraft command"""
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-VL-235B-A22B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_message}],
                },
            ],
            max_tokens=128,
        )
        
        # Access response content directly as shown in the sample
        content = response.choices[0].message.content
        return content.strip()
            
    except Exception as e:
        print(f"Error getting command from Herdora API: {e}")
        return None

if __name__ == "__main__":
    # Check if API key is configured
    if not os.environ.get("HERDORA_API_KEY"):
        print("Error: HERDORA_API_KEY not found in .env file")
        print("Please add your Herdora API key to the .env file:")
        print("HERDORA_API_KEY=your-herdora-api-key-here")
        sys.exit(1)
    
    bot = MinecraftBotAI()
    
    # Run test if no arguments, otherwise run interactive mode
    if len(sys.argv) == 1:
        # Test mode
        print("Running test...")
        cmd = bot.test_command()
        if cmd:
            print("Test completed successfully!")
    else:
        # Interactive mode
        bot.run_interactive()
