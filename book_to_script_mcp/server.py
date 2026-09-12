# -*- coding: utf-8 -*-
"""MCP server exposing the Book-to-Screen app's functions as AI tools.

Run with:  python server.py
Then connect from VS Code by adding this server to .vscode/settings.json.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import book_to_script_app as bts

from mcp.server import MCPServer

server = MCPServer(
    name="book-to-screen",
    instructions=(
        "Tools for the Book-to-Screen app. Use generate_script to build a script "
        "from pasted text, list_presets / get_preset to browse presets, and "
        "format_image_prompt to format an image prompt."
    ),
)


@server.tool(name="generate_script", description="Generate a script/storyboard outline from pasted book text using the saved AI provider/model.")
def generate_script(text: str) -> str:
    if not text.strip():
        return "Error: no text provided."
    cfg = bts.load_config()
    try:
        raw = bts.call_ai(cfg["base_url"], cfg["model"], text)
    except Exception as e:
        return f"AI error: {e}"
    sections = bts.parse_sections(raw)
    blocks = [f"# {s}\n\n{sections[s]}" for s in bts.SECTIONS if sections[s]]
    return ("\n\n---\n\n".join(blocks) if blocks else raw)


@server.tool(name="list_presets", description="List all built-in prompt presets.")
def list_presets() -> str:
    return "\n".join(n for n, _ in bts.PRESETS)


@server.tool(name="get_preset", description="Get the full prompt text for a preset by name.")
def get_preset(name: str) -> str:
    for n, p in bts.PRESETS:
        if n.lower() == name.lower():
            return p
    return f"Unknown preset: {name}"


@server.tool(name="format_image_prompt", description="Format text into an image-engine prompt.")
def format_image_prompt(engine: str, text: str) -> str:
    return bts.format_image_prompt(engine, text)


@server.tool(name="parse_sections", description="Parse raw AI output into the app's sections.")
def parse_sections(text: str) -> str:
    return bts.parse_sections(text or "")


if __name__ == "__main__":
    server.run()
