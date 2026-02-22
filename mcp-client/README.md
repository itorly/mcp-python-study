# Setting Up Your Environment
First, create a new Python project with uv:
```sh
# windows
# Create project directory
uv init mcp-client
cd mcp-client

# Create virtual environment
uv venv
## Output
# Using CPython 3.12.4 interpreter at: ANACONDA3_DIRECTORY\python.exe
# Creating virtual environment at: .venv
# Activate with: .venv\Scripts\activate

# Activate virtual environment
.venv\Scripts\activate

# Install required packages
uv add mcp anthropic python-dotenv

# Remove boilerplate files
del main.py

# Create our main file
new-item client.py
```

# Setting Up Your API Key
```sh
echo "ANTHROPIC_API_KEY=your-api-key-goes-here" > .env
```