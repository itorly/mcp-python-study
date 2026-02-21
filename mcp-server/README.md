# Set up the environment
## Windows
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

 # create and set up the project
 ## Windows
 ```sh
 # Create a new directory for our project
uv init weather
cd weather

# Create virtual environment and activate it
uv venv
.venv\Scripts\activate

# Install dependencies
uv add mcp[cli] httpx

# Create our server file
new-item weather.py
```

# Building a MCP server
weather.py

# Testing the MCP server with Claude for Desktop
We’ll need to configure Claude for Desktop for whichever MCP servers you want to use. To do this, open your Claude for Desktop App configuration.
## Windows
```sh
# What does "code $env:AppData\Claude\claude_desktop_config.json" mean?

# 1.code is the command to open VS Code from the terminal. When you install VS Code, it adds this shortcut to your system.
# 2.$env:AppData is a Windows PowerShell shortcut for your AppData folder path, which is typically C:\Users\YourUsername\AppData\Roaming. 
# So the full path expands to something like C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json.
# 3.The whole command simply means: "Open that config file in VS Code."
code $env:AppData\Claude\claude_desktop_config.json
```

You’ll then add your servers in the mcpServers key. The MCP UI elements will only show up in Claude for Desktop if at least one server is properly configured.

In this case, we’ll add our single weather server like so:
```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\weather",
        "run",
        "weather.py"
      ]
    }
  }
}
```

