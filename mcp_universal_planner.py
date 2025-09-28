#!/usr/bin/env python3
"""
MCP Universal Planner
Converts ANY instruction into detailed step-by-step plans with multiple tool calls
Handles constructions, movement, interactions, and any other Minecraft activities
"""

import os
import json
import subprocess
import sys
import signal
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

UNIVERSAL_PLANNER_PROMPT = """You are an expert Minecraft bot controller connected to an MCP server. For **ANY instruction**, no matter how complex or simple:

1. **Always generate a complete sequence of tool calls** that fully executes the task.
2. **Do not output plans as text** - only execute via tool calls.
3. **Standard Minecraft commands** (like /fill, /tp, /say, /gamemode, etc.) must be sent using the `send-chat` tool.
4. **Available tools**:
   - get-position, move-to-position, look-at, jump, move-in-direction, fly-to
   - list-inventory, find-item, equip-item
   - place-block, dig-block, get-block-info, find-block
   - find-entity, read-chat, detect-gamemode
   - send-chat (for any /command)

**CRITICAL CONSTRUCTION RULE:**
- **ALWAYS start constructions by creating a flat surface first**
- Use /fill to clear and level the ground before building
- Then build the structure on top of the flat surface
- This ensures proper foundations and prevents floating structures

**For CONSTRUCTIONS, create high-quality, realistic buildings with:**
- **FIRST: Create a flat foundation surface**
- Proper architectural principles and realistic proportions
- Multiple materials and textures (stone, wood, glass, etc.)
- Detailed features: windows, doors, roofs, decorations
- Interior spaces and functional elements
- Use stairs, slabs, fences, and decorative blocks
- Create proper foundations, walls, and roofs
- Add landscaping and environmental details

**For MOVEMENT/FOLLOWING:**
- Get current position first
- Calculate relative movements
- Use appropriate movement tools (walk, fly, jump)
- Handle obstacles and terrain

**For INTERACTIONS:**
- Check inventory and equipment
- Find and interact with entities
- Use appropriate tools for the task

**For ANY TASK:**
- Break down into logical steps
- Use efficient commands
- Handle edge cases and errors
- Always output a JSON array of tool calls

**Construction Examples:**

Simple house (with flat surface):
[
  { "tool": "get-position", "args": {} },
  { "tool": "send-chat", "args": { "message": "/fill ~-6 ~-1 ~-6 ~6 ~-1 ~6 stone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-4 ~ ~-4 ~4 ~3 ~4 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-3 ~1 ~-3 ~3 ~2 ~3 air" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-4 ~1 ~ oak_door" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-2 ~1 ~-4 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~2 ~1 ~-4 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-4 ~4 ~-4 ~4 ~4 ~4 stone_brick_stairs" } }
]

Medieval castle (with flat surface):
[
  { "tool": "get-position", "args": {} },
  { "tool": "send-chat", "args": { "message": "/fill ~-25 ~-1 ~-25 ~25 ~-1 ~25 stone" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-20 ~ ~-20 ~20 ~12 ~20 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-18 ~1 ~-18 ~18 ~11 ~18 air" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-20 ~13 ~-20 ~20 ~13 ~20 stone_brick_stairs" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-12 ~ ~-12 ~-12 ~15 ~-12 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/fill ~12 ~ ~-12 ~12 ~15 ~-12 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-12 ~ ~12 ~-12 ~15 ~12 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/fill ~12 ~ ~12 ~12 ~15 ~12 stone_bricks" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-8 ~1 ~-20 oak_door" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-6 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-4 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~-2 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~0 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~2 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~4 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/setblock ~6 ~2 ~-20 glass_pane" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-20 ~1 ~-8 ~-20 ~1 ~8 stone_brick_wall" } },
  { "tool": "send-chat", "args": { "message": "/fill ~-20 ~2 ~-8 ~-20 ~2 ~8 stone_brick_wall" } }
]

**Movement Examples:**

Follow player:
[
  { "tool": "get-position", "args": {} },
  { "tool": "find-entity", "args": { "entity_type": "player" } },
  { "tool": "move-to-position", "args": { "x": "~", "y": "~", "z": "~" } }
]

**Always output a JSON array of tool calls. No explanations.**

Instruction: "{instruction}"

Respond ONLY with a JSON array of tool calls."""

class MCPUniversalPlanner:
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
    
    def plan_instruction(self, instruction: str) -> list:
        """Convert ANY instruction into a detailed step-by-step plan"""
        try:
            # Replace the placeholder in the prompt with the actual instruction
            prompt = UNIVERSAL_PLANNER_PROMPT.replace("{instruction}", instruction)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": f"Convert this instruction: {instruction}",
                    },
                ],
                max_tokens=1024,  # Increased for more detailed plans
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
            print(f"Error planning instruction: {e}")
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
    
    def send_tool_call(self, tool_call):
        """Send a single tool call to the MCP server"""
        try:
            # Create the JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_call["tool"],
                    "arguments": tool_call["args"]
                }
            }
            
            # Send the request
            request_json = json.dumps(request) + "\n"
            print(f"Sending: {request_json.strip()}")
            
            if self.mcp_process and self.mcp_process.stdin:
                self.mcp_process.stdin.write(request_json)
                self.mcp_process.stdin.flush()
                
                # Read response
                response_line = self.mcp_process.stdout.readline()
                if response_line:
                    print(f"Response: {response_line.strip()}")
                else:
                    print("No response received")
            else:
                print("MCP server not available")
                
        except Exception as e:
            print(f"Error sending tool call: {e}")
    
    def run_interactive(self):
        """Run the interactive universal planner"""
        print("🤖 MCP Universal Planner")
        print("=" * 40)
        print("Enter ANY instruction - constructions, movement, interactions, etc.")
        print("Examples:")
        print("  - 'build a medieval castle'")
        print("  - 'follow me'")
        print("  - 'gather wood and build a house'")
        print("  - 'create a garden with flowers'")
        print("  - 'build a bridge across the river'")
        print("Type 'quit' to exit")
        print("-" * 40)
        
        # Start MCP server
        self.start_mcp_server()
        
        while True:
            try:
                instruction = input("\nEnter instruction: ").strip()
                
                if instruction.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not instruction:
                    continue
                
                print(f"\nPlanning: {instruction}")
                plan = self.plan_instruction(instruction)
                
                if plan:
                    print(f"\nGenerated {len(plan)} tool calls - executing immediately...")
                    
                    for i, tool_call in enumerate(plan, 1):
                        print(f"\nStep {i}/{len(plan)}: {tool_call['tool']}")
                        print(f"Args: {tool_call['args']}")
                        self.send_tool_call(tool_call)
                        time.sleep(0.5)  # Small delay between commands
                    
                    print("\nInstruction completed!")
                else:
                    print("Failed to generate instruction plan")
                    
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    try:
        planner = MCPUniversalPlanner()
        planner.run_interactive()
    except Exception as e:
        print(f"Failed to start universal planner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
