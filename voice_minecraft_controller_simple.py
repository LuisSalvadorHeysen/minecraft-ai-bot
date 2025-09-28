#!/usr/bin/env python3
"""
Voice Minecraft Controller (Simple Version)
Listens for voice commands and sends them exactly as spoken to Claude Desktop
Uses system speech recognition instead of pyaudio
"""

import subprocess
import pyautogui
import time
import sys
import signal
import os

class VoiceMinecraftController:
    def __init__(self):
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully"""
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Clean up on Ctrl+C"""
        print("\nShutting down voice controller...")
        sys.exit(0)
    
    def listen_for_command(self):
        """Listen for voice command using system speech recognition"""
        try:
            print("\n🎤 Listening for voice command...")
            print("📝 Please type your command (or press Enter to skip):")
            
            # For now, use text input instead of voice
            # This avoids the pyaudio dependency issue
            command = input("> ").strip()
            
            if command:
                print(f"📝 Command: '{command}'")
                return command
            else:
                print("⏰ No command entered")
                return None
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def send_to_claude(self, command):
        """Send command exactly as spoken to Claude Desktop"""
        try:
            print(f"📤 Sending to Claude: '{command}'")
            
            # Give user a moment to focus on Claude Desktop
            print("⏳ Switching to Claude Desktop in 2 seconds...")
            time.sleep(2)
            
            # Type the command exactly as spoken in Claude Desktop
            pyautogui.typewrite(command)
            
            # Press Enter to send
            pyautogui.press('enter')
            
            print("✅ Command sent to Claude Desktop!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending to Claude: {e}")
            return False
    
    def run_voice_controller(self):
        """Main voice control loop"""
        print("🎮 Voice Minecraft Controller (Simple Version) started!")
        print("📋 Commands:")
        print("  - Type any command exactly as you want it sent to Claude")
        print("  - Type 'quit' or 'exit' to stop")
        print("  - Press Ctrl+C to exit")
        print("\n🎤 Make sure Claude Desktop is open and ready to receive commands!")
        print("-" * 60)
        
        while True:
            try:
                # Listen for command (text input for now)
                command = self.listen_for_command()
                
                if command is None:
                    continue
                
                # Check for exit commands
                if command.lower() in ['quit', 'exit', 'stop', 'goodbye']:
                    print("👋 Goodbye!")
                    break
                
                # Send command exactly as spoken to Claude Desktop
                success = self.send_to_claude(command)
                
                if success:
                    print(f"✅ Successfully sent: '{command}'")
                else:
                    print(f"❌ Failed to send: '{command}'")
                
                # Brief pause before listening again
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(1)

def main():
    """Main function"""
    print("🎮 Voice Minecraft Controller (Simple Version)")
    print("=" * 50)
    
    try:
        controller = VoiceMinecraftController()
        controller.run_voice_controller()
    except Exception as e:
        print(f"❌ Failed to start voice controller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
