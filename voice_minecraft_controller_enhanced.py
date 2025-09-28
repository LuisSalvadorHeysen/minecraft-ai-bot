#!/usr/bin/env python3
"""
Enhanced Voice Minecraft Controller
- Works with dual monitor setup (Claude on second monitor)
- Longer listening duration after wake word
- Optimized for gaming while using voice commands
"""

import speech_recognition as sr
import pyautogui
import time
import sys
import signal
from datetime import datetime

class EnhancedVoiceMinecraftController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.setup_signal_handlers()
        self.setup_microphone()
        self.wake_word = "hey inga"
        self.is_listening_for_wake = True
        
        # Enhanced settings for better recognition
        self.recognizer.energy_threshold = 300  # Lower threshold for better detection
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Longer pause before considering speech ended
    
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
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Microphone ready!")
    
    def listen_for_wake_word(self):
        """Listen for 'hey inga' wake word with enhanced settings"""
        try:
            print(f"\n🎤 Listening for wake word: '{self.wake_word}'...")
            
            with self.microphone as source:
                # Shorter timeout for wake word detection
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
            
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"📝 Heard: '{text}'")
            return text.strip().lower()
            
        except sr.WaitTimeoutError:
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
    
    def listen_for_command(self):
        """Listen for voice command with extended duration"""
        try:
            print("\n🎤 Listening for command (extended duration)...")
            print("💡 Speak your full command - I'll wait for you to finish...")
            
            with self.microphone as source:
                # Extended listening for complete commands
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
            
            print("🔄 Processing speech...")
            command = self.recognizer.recognize_google(audio)
            print(f"📝 Heard: '{command}'")
            return command.strip()
            
        except sr.WaitTimeoutError:
            print("⏰ No command detected within timeout")
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
        """Send command to Claude Desktop (optimized for second monitor)"""
        try:
            print(f"📤 Sending to Claude: '{command}'")
            
            # Give user time to switch to Claude Desktop
            print("⏳ Switching to Claude Desktop in 3 seconds...")
            print("💡 Make sure Claude Desktop is focused on your second monitor!")
            time.sleep(3)
            
            # Type the command exactly as spoken in Claude Desktop
            pyautogui.typewrite(command)
            
            # Press Enter to send
            pyautogui.press('enter')
            
            print("✅ Command sent to Claude Desktop!")
            print("🎮 You can return to Minecraft now!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending to Claude: {e}")
            return False
    
    def run_voice_controller(self):
        """Main voice control loop optimized for gaming"""
        print("🎮 Enhanced Voice Minecraft Controller")
        print("=" * 50)
        print("📋 Setup Instructions:")
        print("  1. Claude Desktop should be open on your second monitor")
        print("  2. Minecraft should be running on your main monitor")
        print("  3. Say 'hey inga' to activate")
        print("  4. Then speak your full command")
        print("  5. Say 'quit' or 'exit' to stop")
        print("  6. Press Ctrl+C to exit")
        print("\n🎤 Optimized for gaming - longer listening duration!")
        print("-" * 60)
        
        while True:
            try:
                if self.is_listening_for_wake:
                    # Listen for wake word
                    text = self.listen_for_wake_word()
                    
                    if text is None:
                        continue
                    
                    # Check if wake word was detected
                    if self.wake_word in text:
                        print(f"✅ Wake word '{self.wake_word}' detected!")
                        print("🎤 Ready for your command...")
                        self.is_listening_for_wake = False
                        time.sleep(0.5)  # Brief pause before listening for command
                        continue
                    else:
                        print(f"❌ Wake word not detected. Expected: '{self.wake_word}'")
                        continue
                
                else:
                    # Listen for command after wake word with extended duration
                    command = self.listen_for_command()
                    
                    if command is None:
                        print("🔄 Returning to wake word listening...")
                        self.is_listening_for_wake = True
                        continue
                    
                    # Check for exit commands
                    if command.lower() in ['quit', 'exit', 'stop', 'goodbye']:
                        print("👋 Goodbye!")
                        break
                    
                    # Send command to Claude Desktop
                    success = self.send_to_claude(command)
                    
                    if success:
                        print(f"✅ Successfully sent: '{command}'")
                    else:
                        print(f"❌ Failed to send: '{command}'")
                    
                    # Return to wake word listening
                    print("🔄 Returning to wake word listening...")
                    self.is_listening_for_wake = True
                    time.sleep(2)  # Longer pause to avoid accidental activation
                
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(1)

def main():
    """Main function"""
    print("🎮 Enhanced Voice Minecraft Controller")
    print("=" * 50)
    
    try:
        controller = EnhancedVoiceMinecraftController()
        controller.run_voice_controller()
    except Exception as e:
        print(f"❌ Failed to start voice controller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
