# Voice Minecraft Controller

A simple voice-controlled system that listens for voice commands and sends them exactly as spoken to Claude Desktop.

## Features

- 🎤 **Voice Recognition** - Listens for voice commands using Google Speech Recognition
- 🤖 **Claude Integration** - Automatically types commands exactly as spoken into Claude Desktop
- ⚡ **Real-time Processing** - Continuous listening with timeout handling
- 🛡️ **Error Handling** - Robust error handling for speech recognition issues
- 🚫 **No API Keys** - No external API keys required, just voice recognition

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_voice.txt
```

### 2. System Requirements

- **Microphone** - Working microphone for voice input
- **Claude Desktop** - Must be open and ready to receive commands
- **Internet Connection** - Required for Google Speech Recognition

### 3. Audio Setup

Make sure your microphone is working:
```bash
# Test microphone (optional)
python -c "import speech_recognition as sr; print('Microphone test:', sr.Microphone().list_microphone_names())"
```

## Usage

### 1. Start the Voice Controller

```bash
python voice_minecraft_controller.py
```

### 2. Voice Commands

Simply speak your commands exactly as you want them sent to Claude:

**Examples:**
- "build a house" → Sends "build a house"
- "create a castle with towers" → Sends "create a castle with towers"
- "make a bridge across the river" → Sends "make a bridge across the river"
- "construct a modern skyscraper" → Sends "construct a modern skyscraper"

### 3. Exit Commands

Say any of these to stop:
- "quit"
- "exit"
- "stop"
- "goodbye"

Or press **Ctrl+C**

## How It Works

1. **🎤 Listens** - Continuously listens for voice input
2. **🔄 Processes** - Uses Google Speech Recognition to convert speech to text
3. **📝 Transcribes** - Shows what was heard
4. **⏳ Waits** - Gives 2 seconds to focus on Claude Desktop
5. **📤 Types** - Automatically types the command exactly as spoken
6. **✅ Sends** - Presses Enter to send to Claude

## Example Session

```
🎮 Voice Minecraft Controller started!
📋 Commands:
  - Say any command exactly as you want it sent to Claude
  - Say 'quit' or 'exit' to stop
  - Press Ctrl+C to exit

🎤 Make sure Claude Desktop is open and ready to receive commands!
------------------------------------------------------------

🎤 Listening for voice command...
🔄 Processing speech...
📝 Heard: 'build a house'
📤 Sending to Claude: 'build a house'
⏳ Switching to Claude Desktop in 2 seconds...
✅ Command sent to Claude Desktop!
✅ Successfully sent: 'build a house'

🎤 Listening for voice command...
```

## Troubleshooting

### Common Issues

1. **"Could not understand speech"**
   - Speak more clearly and slowly
   - Check microphone is working
   - Reduce background noise

2. **"Speech recognition error"**
   - Check internet connection
   - Google Speech Recognition requires internet

3. **"Error sending to Claude"**
   - Make sure Claude Desktop is open
   - Check that Claude Desktop is focused/active
   - Ensure pyautogui has permission to control the system

### System Permissions

On macOS, you may need to grant accessibility permissions to Python/terminal for pyautogui to work.

## File Structure

```
voice_minecraft_controller.py  # Main voice controller
requirements_voice.txt        # Python dependencies
README_voice.md              # This documentation
```

## Dependencies

- **SpeechRecognition** - Speech-to-text conversion
- **pyautogui** - GUI automation for typing
- **pyaudio** - Audio input handling

## Tips for Best Results

1. **Clear Speech** - Speak clearly and at normal pace
2. **Quiet Environment** - Reduce background noise
3. **Claude Ready** - Keep Claude Desktop open and ready
4. **Natural Commands** - Speak naturally, the system will send exactly what you say
5. **Pause Between** - Wait for processing before next command

## Key Changes

- ✅ **No API keys required** - Uses only Google Speech Recognition (free)
- ✅ **Exact transcription** - Sends commands exactly as spoken
- ✅ **No modifications** - No "in minecraft" suffix or other changes
- ✅ **Simple setup** - Just install dependencies and run
