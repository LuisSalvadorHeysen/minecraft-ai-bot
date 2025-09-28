# Minecraft AI Bot with Herdora API

A Python integration that controls a Minecraft MCP server bot using Herdora's Qwen model for natural language to Minecraft command conversion.

## Features

- 🤖 **Herdora API Integration** - Uses Qwen/Qwen3-VL-235B-A22B-Instruct model
- 🎮 **Minecraft Command Generation** - Converts natural language to valid Minecraft commands
- 🔗 **MCP Server Integration** - Directly executes commands in Minecraft via MCP server
- 🛡️ **Error Handling** - Robust error handling for API failures and connection issues
- 🎯 **Interactive Mode** - Real-time command processing from terminal input
- 🧪 **Test Mode** - Built-in testing functionality

## Setup Instructions

### 1. Install Dependencies

```bash
pip install openai python-dotenv
```

### 2. Configure API Key

Edit the `.env` file and add your Herdora API key:

```bash
HERDORA_API_KEY=your-actual-herdora-api-key-here
```

### 3. MCP Server Setup

You have two options:

**Option A: Automatic (if you have index.js)**
- Place your `index.js` MCP server file in the same directory
- The bot will automatically start the MCP server

**Option B: Manual**
- Run your MCP server separately before starting the bot
- The bot will connect to the existing server

## Usage

### Test Mode (Default)
```bash
python bot_ai.py
```
This runs a test with the command "Teleport me to 100 64 -200" and shows the generated Minecraft command.

### Interactive Mode
```bash
python bot_ai.py interactive
```
This starts an interactive session where you can type natural language commands.

### Example Session
```
$ python bot_ai.py
Testing with: 'Teleport me to 100 64 -200'
AI Minecraft Command: /tp @p 100 64 -200
Test completed successfully!

$ python bot_ai.py interactive
Minecraft AI Bot (Herdora) started. Type instructions:
(Press Ctrl+C to exit)

> build me a house
AI Minecraft Command: /fill ~ ~ ~ ~10 ~5 ~10 stone
Command sent to MCP server

> give me some diamonds
AI Minecraft Command: /give @p diamond 10
Command sent to MCP server
```

## Supported Commands

The AI can generate various Minecraft commands including:

- `/tp @p <x> <y> <z>` - Teleport player
- `/fill <x1> <y1> <z1> <x2> <y2> <z2> <block>` - Fill area with blocks
- `/clone <x1> <y1> <z1> <x2> <y2> <z2> <x> <y> <z>` - Clone blocks
- `/setblock <x> <y> <z> <block>` - Set single block
- `/summon <entity> <x> <y> <z>` - Summon entities
- `/give @p <item> <count>` - Give items to player
- `/say <message>` - Send chat message

## File Structure

```
minecraft-bot/
├── bot_ai.py          # Main bot controller
├── controller.py      # Original OpenAI controller (legacy)
├── requirements.txt   # Python dependencies
├── .env              # Environment variables
└── README.md         # This file
```

## API Configuration

The bot uses the following Herdora API settings:
- **Base URL**: `https://pygmalion.herdora.com/v1`
- **Model**: `Qwen/Qwen3-VL-235B-A22B-Instruct`
- **Max Tokens**: 128
- **System Prompt**: Optimized for Minecraft command generation

## Error Handling

The bot includes comprehensive error handling:
- API connection failures
- Invalid API responses
- MCP server connection issues
- Missing dependencies
- Graceful shutdown on Ctrl+C

## Troubleshooting

### Common Issues

1. **"HERDORA_API_KEY not found"**
   - Make sure your `.env` file contains the correct API key
   - Check that the key is valid and active

2. **"Node.js not found"**
   - Install Node.js or run the MCP server manually
   - The bot will still work in command-only mode

3. **"MCP server not available"**
   - Ensure your MCP server is running
   - Check that `index.js` exists if using automatic mode

### Getting Help

If you encounter issues:
1. Check the error messages in the terminal
2. Verify your API key is correct
3. Ensure all dependencies are installed
4. Make sure the MCP server is properly configured
