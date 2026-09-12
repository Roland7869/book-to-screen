Book-to-Screen — AI tools (MCP server)
=======================================

This folder contains a small "AI helper" for the Book-to-Screen app. It lets
AI tools (like GitHub Copilot in VS Code) call the app's functions — generate a
script, browse presets, format image prompts — as if they were buttons.

How to use it (simple steps):
-----------------------------
1. Make sure your API key is saved in the Book-to-Screen app
   (Tab 1 -> "Save key"). The helper uses that same key.

2. Open the Book-to-Screen project folder in VS Code.
   You should see book_to_script_app.py in the file list.

3. In VS Code, press Ctrl+,  then search "Enable MCP Servers" and turn it ON.

4. The AI tools are now available to Copilot automatically.
   (No other installation needed — VS Code has MCP built in.)

What the tools do:
------------------
- generate_script  : turn pasted book text into a script
- list_presets     : see all built-in prompt styles
- get_preset       : get one prompt style's full text
- format_image_prompt : turn text into an image prompt
- parse_sections   : split AI text into sections

Do NOT edit these files unless you know what you are doing:
- server.py
- (the settings.json in the .vscode folder)
