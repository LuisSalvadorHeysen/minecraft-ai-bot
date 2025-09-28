#!/usr/bin/env python3
"""
Voice Minecraft Controller
Listens for voice commands and sends them exactly as spoken to Claude Desktop
"""

import speech_recognition as sr
import pyautogui
import time
import sys
import signal
from datetime import datetime

class VoiceMinecraftController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.setup_signal_handlers()
        self.setup_microphone()
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully"""
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Clean up on Ctrl+C"""
        print("\nShutting down voice controller...")
        sys.exit(0)
    
    def setup_microphone(self):
        """Initialize microphone and adjust for ambient noise"""
        print("Setting up microphone...")
        with self.microphone as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone ready!")
    
    def listen_for_command(self):
        """Listen for voice command and return transcribed text"""
        try:
            print("\n🎤 Listening for voice command...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            # Use Google's speech recognition
            command = self.recognizer.recognize_google(audio)
            print(f"📝 Heard: '{command}'")
            return command.strip()
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand speech")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
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
        print("🎮 Voice Minecraft Controller started!")
        print("📋 Commands:")
        print("  - Say any command exactly as you want it sent to Claude")
        print("  - Say 'quit' or 'exit' to stop")
        print("  - Press Ctrl+C to exit")
        print("\n🎤 Make sure Claude Desktop is open and ready to receive commands!")
        print("-" * 60)
        
        while True:
            try:
                # Listen for voice command
                command = self.listen_for_command()
                
                if command is None:
                    continue
                
                # Check for exit commands
                if command.lower() in ['quit', 'exit', 'stop', 'goodbye']:
                    print("�� Goodbye!")
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
    print("🎮 Voice Minecraft Controller")
    print("=" * 40)
    
    try:
        controller = VoiceMinecraftController()
        controller.run_voice_controller()
    except Exception as e:
        print(f"❌ Failed to start voice controller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
