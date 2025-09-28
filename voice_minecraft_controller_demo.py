#!/usr/bin/env python3
"""
Enhanced Voice Minecraft Controller for Demo
Uses speech-to-text and sends commands to Claude Desktop
Supports both Google Speech Recognition and OpenAI Whisper
"""

import speech_recognition as sr
import pyautogui
import time
import sys
import signal
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class EnhancedVoiceMinecraftController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.setup_signal_handlers()
        self.setup_microphone()
        self.wake_word = "hey inga"
        self.is_listening_for_wake = True
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if os.environ.get("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            print("✅ OpenAI API available for Whisper speech recognition")
        else:
            print("⚠️  OpenAI API key not found - using Google Speech Recognition only")
        
        # Enhanced settings for better recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
    
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
    
    def transcribe_audio_google(self, audio):
        """Transcribe audio using Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Google Speech Recognition error: {e}")
            return None
    
    def transcribe_audio_whisper(self, audio):
        """Transcribe audio using OpenAI Whisper API"""
        if not self.openai_client:
            return None
        
        try:
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio.export(tmp_file.name, format="wav")
                
                # Transcribe using Whisper
                with open(tmp_file.name, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                return transcript.text.strip()
                
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return None
    
    def listen_for_wake_word(self):
        """Listen for 'hey inga' wake word with enhanced settings"""
        try:
            print(f"\n🎤 Listening for wake word: '{self.wake_word}'...")
            
            with self.microphone as source:
                # Shorter timeout for wake word detection
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=3)
            
            print("🔄 Processing speech...")
            
            # Try OpenAI Whisper first (if available), then Google
            text = None
            if self.openai_client:
                print("🎯 Trying OpenAI Whisper...")
                text = self.transcribe_audio_whisper(audio)
            
            if not text:
                print("🎯 Trying Google Speech Recognition...")
                text = self.transcribe_audio_google(audio)
            
            if text:
                print(f"📝 Heard: '{text}'")
                return text.strip().lower()
            else:
                print("❓ Could not understand speech")
                return None
            
        except sr.WaitTimeoutError:
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
            
            # Try OpenAI Whisper first (if available), then Google
            text = None
            if self.openai_client:
                print("🎯 Trying OpenAI Whisper...")
                text = self.transcribe_audio_whisper(audio)
            
            if not text:
                print("🎯 Trying Google Speech Recognition...")
                text = self.transcribe_audio_google(audio)
            
            if text:
                print(f"📝 Heard: '{text}'")
                return text.strip()
            else:
                print("❓ Could not understand speech")
                return None
            
        except sr.WaitTimeoutError:
            print("⏰ No command detected within timeout")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def send_to_claude(self, command):
        """Send command to Claude Desktop"""
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
        """Main voice control loop optimized for demo"""
        print("🎮 Enhanced Voice Minecraft Controller (Demo Version)")
        print("=" * 60)
        print("📋 Demo Setup:")
        print("  1. Claude Desktop should be open on your second monitor")
        print("  2. Minecraft should be running on your main monitor")
        print("  3. Say 'hey inga' to activate")
        print("  4. Then speak your full command")
        print("  5. Say 'quit' or 'exit' to stop")
        print("  6. Press Ctrl+C to exit")
        print("\n🎤 Speech Recognition Methods:")
        if self.openai_client:
            print("  ✅ OpenAI Whisper (primary)")
            print("  ✅ Google Speech Recognition (fallback)")
        else:
            print("  ✅ Google Speech Recognition")
        print("\n🎤 Optimized for demo - longer listening duration!")
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
    print("🎮 Enhanced Voice Minecraft Controller (Demo)")
    print("=" * 50)
    
    try:
        controller = EnhancedVoiceMinecraftController()
        controller.run_voice_controller()
    except Exception as e:
        print(f"❌ Failed to start voice controller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
