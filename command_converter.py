#!/usr/bin/env python3
"""
Minecraft Command Converter
Converts high-level instructions into JSON arrays of Minecraft commands
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

CONVERSION_PROMPT = """You are controlling a Minecraft bot.  
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

Instruction: "{instruction}"

Respond ONLY with a JSON array of Minecraft commands."""

def convert_instruction_to_commands(instruction: str) -> list:
    """Convert a high-level instruction into a list of Minecraft commands"""
    try:
        # Replace the placeholder in the prompt with the actual instruction
        prompt = CONVERSION_PROMPT.replace("{instruction}", instruction)
        
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
    """Interactive command converter"""
    if not os.environ.get("HERDORA_API_KEY"):
        print("Error: HERDORA_API_KEY not found in .env file")
        return
    
    print("Minecraft Command Converter")
    print("Type 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            instruction = input("\nEnter instruction: ").strip()
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                break
                
            if not instruction:
                continue
            
            print(f"\nConverting: '{instruction}'")
            commands = convert_instruction_to_commands(instruction)
            
            if commands:
                print("\nGenerated commands:")
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
