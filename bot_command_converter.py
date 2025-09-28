#!/usr/bin/env python3
"""
Minecraft Bot Command Converter
Converts high-level instructions into JSON arrays of bot commands
"""

import os
import json
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

BOT_COMMAND_PROMPT = """You are controlling a Minecraft bot.  
Your task is to convert high-level instructions into a **JSON array of valid bot commands** that Claude can execute.  

**Rules:**
1. Output ONLY a JSON array of strings. No explanations, no natural language.  
2. There are two types of commands:

**A) Bot-native commands** (use these directly):
Movement:
- "get-position"  
- "move-to-position x y z"  
- "look-at x y z"  
- "jump"  
- "move-in-direction direction duration"  

Flight:
- "fly-to x y z"  

Inventory:
- "list-inventory"  
- "find-item item_name"  
- "equip-item item_name"  

Block Interaction:
- "place-block x y z block_type"  
- "dig-block x y z"  
- "get-block-info x y z"  
- "find-block block_type"  

Entity Interaction:
- "find-entity entity_type"  

Communication:
- "read-chat"  

Game State:
- "detect-gamemode"  

**B) Vanilla Minecraft commands** (send these as chat messages using `send-chat`):
- Any command starting with `/` (e.g., `/fill`, `/tp`, `/gamemode creative`, `/say message`)  
- Format: `"send-chat /command_here"`  

3. If coordinates are required but not specified, use the bot's current position as reference.  
4. Always handle multi-step instructions as a **sequence of commands**.  

**Example**:

Instruction: "Teleport to (100, 64, 200) and fill a 5x5x5 cube of stone at that location"

JSON output:
[
  "send-chat /tp @p 100 64 200",
  "send-chat /fill 100 64 200 104 68 204 stone"
]

Instruction: "{instruction}"

Respond ONLY with a JSON array of bot commands."""

def convert_instruction_to_bot_commands(instruction: str) -> list:
    """Convert a high-level instruction into a list of bot commands"""
    try:
        # Replace the placeholder in the prompt with the actual instruction
        prompt = BOT_COMMAND_PROMPT.replace("{instruction}", instruction)
        
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

def main():
    """Interactive bot command converter"""
    if not os.environ.get("HERDORA_API_KEY"):
        print("Error: HERDORA_API_KEY not found in .env file")
        return
    
    print("Minecraft Bot Command Converter")
    print("Converts instructions into JSON arrays of bot commands")
    print("Type 'quit' to exit")
    print("-" * 50)
    
    while True:
        try:
            instruction = input("\nEnter instruction: ").strip()
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                break
                
            if not instruction:
                continue
            
            print(f"\nConverting: '{instruction}'")
            commands = convert_instruction_to_bot_commands(instruction)
            
            if commands:
                print("\nGenerated bot commands:")
                print(json.dumps(commands, indent=2))
                
                # Show individual commands
                print(f"\n{len(commands)} commands to execute:")
                for i, cmd in enumerate(commands, 1):
                    print(f"{i}. {cmd}")
            else:
                print("Failed to convert instruction")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
