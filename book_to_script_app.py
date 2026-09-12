# -*- coding: utf-8 -*-
"""Book-to-Screen AI Production Pipeline — standalone desktop app.

Tab 1: Paste prose -> AI -> parse into Prose / Environment / Mood & Lighting /
       Characters / Spoken Dialogue, plus an image-engine prompt and editable beats.
Tab 2: Link pictures / text / environment picture, choose a video model and
       runtime, then assemble a storyboard.
Tab 3: Browse and manage prompt presets.
Tab 4: Launch browser-based Scene Canvas planner.
Tab 5: Character Sheet Creator — browse Obsidian vault, select files,
       generate comprehensive character sheets with AI.

Run with:  python book_to_script_app.py
Or compile to a single .exe with compile_exe.bat (no Python required).
"""

import os
import json
import re
import threading
import requests
from pathlib import Path
from urllib.parse import quote

import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, Scrollbar

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"

# --------------------------------------------------------------------------- #
# Configuration / data
# --------------------------------------------------------------------------- #
IMAGE_ENGINES = [
    "Z-Image Turbo (Amuse)",
    "LTX Studio",
    "SEEDANCE 2.5",
    "Midjourney",
    "Flux",
    "DALL·E 3",
]
VIDEO_MODELS = [
    "LTX 2.3",
    "SEEDANCE 2.5",
    "Runway Gen-4",
    "Kling",
    "Hailuo (MiniMax)",
    "Sora",
]
RUNTIME_PRESETS = ["3 min", "5 min", "7 min", "10 min", "Custom…"]
NUM_BEATS = 6

SECTIONS = ["PROSE", "ENVIRONMENT", "MOOD AND LIGHTING", "CHARACTERS", "SPOKEN DIALOGUE"]

PRESETS = [
    ("Cinematic & Detailed", "You are a meticulous film director. Break the source into rich, cinematic 20-second scenes with heavy attention to atmosphere, lighting, and emotional detail. Include vivid environmental descriptions, character micro-expressions, and layered sound design."),
    ("Minimal Screenplay", "You are a minimalist screenwriter. Keep scenes tight and visual. Focus on essential action and dialogue only — cut all unnecessary description. Show, don't tell. Fast pacing."),
    ("Dialogue-Heavy", "You are a dialogue-focused screenwriter. Emphasize conversations, subtext, and vocal performance. Keep action brief; let the characters speak. Include emotional beats between lines."),
    ("Atmosphere-Focused", "You are an atmosphere-focused director. Prioritize mood, lighting, and environment over plot. Describe how light, weather, and space shape each scene. Slow, immersive pacing."),
    ("Character-First", "You are a character-driven screenwriter. Focus on internal states, motivation, and character arcs. Show emotions through physical detail and behavior. Prioritize how characters feel and change."),
]

CUSTOM_PATH = APP_DIR / "custom_prompts.json"
CHARACTER_SHEET_PROMPT_PATH = APP_DIR / "character_sheet_prompt.md"
SCRIPT_WRITER_PROMPT_PATH = APP_DIR / "script_writer_prompt.md"
DEFAULT_VAULT_PATH = r"C:\Books\Books\Books"


def load_config():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {
            "model": data.get("model", ""),
            "base_url": data.get("base_url", "http://127.0.0.1:1235/v1"),
            "local_ai": data.get("local_ai", True),
            "appearance": data.get("appearance", "Light"),
        }
    except Exception:
        return {"model": "", "base_url": "http://127.0.0.1:1235/v1",
                "local_ai": True, "appearance": "Light"}


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# AI API layer (local OpenAI-compatible server, e.g. Ollama at :1235/v1)
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """You are an expert film director, screenwriter and storyboard artist
adapting a book or prose text into a 20-second-per-scene video production.

Break the source text below into the following sections. Use these exact headers
(one line each, ALL CAPS, preceded by a single '#'):

# PROSE
# ENVIRONMENT
# MOOD AND LIGHTING
# CHARACTERS
# SPOKEN DIALOGUE

Rules:
- PROSE: a tight, present-tense, visual 'show don't tell' screenplay action
  description of the source material.
- ENVIRONMENT: every location — architecture, surfaces, time of day, atmosphere,
  colour palette, recurring elements.
- MOOD AND LIGHTING: emotional tone plus lighting (direction, quality, colour
  temperature, atmosphere/light interaction).
- CHARACTERS: cast list with age, key physical traits, wardrobe, distinguishing
  features, and first appearance.
- SPOKEN DIALOGUE: exact dialogue and/or narration, who speaks it, emotional
  state and vocal quality.
Be specific and sensory. Do not invent events that contradict the source."""


def call_ai(base_url, model, user_text, timeout=1400, custom_prompt=None):
    """Call the local OpenAI-compatible server (e.g. Ollama-style at :1235/v1)."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if model:
        body = {"model": model, "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": custom_prompt or SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ]}
    else:
        body = {"temperature": 0.7,
                "messages": [
                    {"role": "system", "content": custom_prompt or SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ]}
    r = requests.post(url, json=body, headers=headers, timeout=timeout)
    return r.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------- #
# Output parsing
# --------------------------------------------------------------------------- #
def _is_header(line):
    return line.strip().lstrip("#").strip()


def parse_sections(text):
    result = {s: "" for s in SECTIONS}
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        norm = _is_header(lines[i])
        matched = False
        for s in SECTIONS:
            if norm.startswith(s):
                j = i + 1
                while j < n:
                    if _is_header(lines[j]).startswith(tuple(SECTIONS + ["BEATS"])):
                        break
                    j += 1
                result[s] = "\n".join(lines[i + 1:j]).strip()
                i = j
                matched = True
                break
        if not matched:
            i += 1
    return result


def parse_beats(text):
    scenes = []
    for m in re.finditer(r'<scene\s+number="(\d+)"(.*?)(?=<scene\s+number=|$)', text, re.DOTALL | re.IGNORECASE):
        scene_num = m.group(1)
        scene_body = m.group(2).strip()
        slug = ""
        slug_m = re.search(r"<slugline>(.*?)</slugline>", scene_body, re.IGNORECASE | re.DOTALL)
        if slug_m:
            slug = slug_m.group(1).strip()
        purpose = ""
        purpose_m = re.search(r"<primary>(.*?)</primary>", scene_body, re.IGNORECASE | re.DOTALL)
        if purpose_m:
            purpose = purpose_m.group(1).strip()
        chars = ""
        chars_m = re.search(r"<characters>(.*?)</characters>", scene_body, re.IGNORECASE | re.DOTALL)
        if chars_m:
            chars = chars_m.group(1).strip()
        summary = f"Scene {scene_num}"
        if slug:
            summary += f" | {slug}"
        if purpose:
            summary += f" | {purpose}"
        if chars:
            summary += f" | {chars}"
        scenes.append(summary)
    if scenes:
        return scenes[:NUM_BEATS]
    for m in re.finditer(r"###\s+Scene\s+(\d+)(.*?)(?=###\s+Scene\s+\d+|$)", text, re.DOTALL | re.IGNORECASE):
        scene_num = m.group(1)
        scene_body = m.group(2).strip()
        slug = ""
        slug_m = re.search(r"Slugline[:\s]*(.+)", scene_body, re.IGNORECASE)
        if slug_m:
            slug = slug_m.group(1).strip().strip("`")
        purpose = ""
        purpose_m = re.search(r"Narrative Purpose[:\s]*(.+)", scene_body, re.IGNORECASE)
        if purpose_m:
            purpose = purpose_m.group(1).strip()
        chars = ""
        chars_m = re.search(r"\*?\*?Characters[:\s]*(.+)", scene_body, re.IGNORECASE)
        if chars_m:
            chars = chars_m.group(1).strip()
        summary = f"Scene {scene_num}"
        if slug:
            summary += f" | {slug}"
        if purpose:
            summary += f" | {purpose}"
        if chars:
            summary += f" | {chars}"
        scenes.append(summary)
    if scenes:
        return scenes[:NUM_BEATS]
    idx = text.upper().find("BEATS")
    if idx == -1:
        return []
    lines = [l.strip() for l in text[idx:].splitlines() if l.strip()]
    if lines and lines[0].upper().replace(":", "").strip() == "BEATS":
        lines = lines[1:]
    beats = []
    current = []
    for l in lines:
        num = re.search(r"(beat\s*)?(\d+)[\.):]?\s*(.*)", l, re.IGNORECASE)
        if num:
            if current:
                beats.append(" ".join(current))
            current = [num.group(3)]
        else:
            current.append(l)
    if current:
        beats.append(" ".join(current))
    return [b for b in beats if b][:NUM_BEATS]


# --------------------------------------------------------------------------- #
# Image prompt formatting
# --------------------------------------------------------------------------- #
def clean_screenplay_output(text):
    clean = text
    clean = re.sub(r'<scene\s+number="(\d+)"[^>]*>', r'\n\n=== SCENE \1 ===\n', clean)
    clean = re.sub(r'</scene>', '\n---', clean)
    clean = re.sub(r'<slugline>(.*?)</slugline>', r'Slugline: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<location>(.*?)</location>', r'Location: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<time_of_day>(.*?)</time_of_day>', r'Time: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<primary_pov>(.*?)</primary_pov>', r'POV: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<storytelling_mode>(.*?)</storytelling_mode>', r'Mode: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<primary>(.*?)</primary>', r'Purpose: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<secondary>(.*?)</secondary>', r'Secondary: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<narrative_weight>(.*?)</narrative_weight>', r'Weight: \1/10', clean, flags=re.DOTALL)
    clean = re.sub(r'<characters>(.*?)</characters>', r'Characters: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<mood>(.*?)</mood>', r'Mood: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<visual>(.*?)</visual>', r'  - \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<type>(.*?)</type>', r'Transition: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'<motivation>(.*?)</motivation>', r'Reason: \1', clean, flags=re.DOTALL)
    clean = re.sub(r'</?character_state[^>]*>', '', clean)
    clean = re.sub(r'</?character_states>', '', clean)
    clean = re.sub(r'</?props>', '', clean)
    clean = re.sub(r'</?prop[^>]*>', '', clean)
    clean = re.sub(r'</?key_visuals>', '', clean)
    clean = re.sub(r'</?narrative_pov>', '', clean)
    clean = re.sub(r'</?beat_purpose>', '', clean)
    clean = re.sub(r'</?story_information>', '', clean)
    clean = re.sub(r'</?canon>', '', clean)
    clean = re.sub(r'</?visual_interpretation>', '', clean)
    clean = re.sub(r'</?transition_in>', '', clean)
    clean = re.sub(r'</?transition_out>', '', clean)
    clean = re.sub(r'<\w+>[^<]*</\w+>', '', clean)
    clean = re.sub(r'<[^>]+>', '', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = clean.strip()
    return clean


def format_image_prompt(engine, text):
    t = text.strip()
    if not t:
        return ""
    if engine == "Z-Image Turbo (Amuse)":
        return (f"Photorealistic, subject first: {t}. Order subject -> wardrobe/ "
                f"expression -> lighting -> background -> camera/film anchor last. "
                f"No negative prompts. 80-250 words. One camera/lens/film style "
                f"anchor only.")
    if engine == "Midjourney":
        return f"{t} --ar 16:9 --style raw --q 2"
    if engine == "Flux":
        return f"Prompt: {t} (photorealistic, cinematic lighting, film grain)"
    if engine == "DALL·E 3":
        return f"{t}"
    if engine == "LTX Studio":
        return f"{t} (cinematic still, 35mm, shallow depth of field, film grain)"
    if engine == "SEEDANCE 2.5":
        return f"{t} (21:9, photorealistic, cinematic color grade, 24fps)"
    return t


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
class BookToScriptApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Book-to-Screen AI Production Pipeline")
        self.geometry("1180x760")
        self.minsize(1000, 680)
        self._set_icon()
        cfg = load_config()
        self.local_ai = bool(cfg.get("local_ai", False))
        self.base_url = cfg.get("base_url", "http://127.0.0.1:1235/v1")
        self.model = cfg.get("model", "")
        self.appearance = cfg.get("appearance", "Light")
        ctk.set_appearance_mode(self.appearance)
        self.dark_mode_var = ctk.BooleanVar(value=False)
        self.custom_prompt = ""
        self.prompt_path = ""
        self.custom_prompts = list(self._load_custom_prompts())
        self.custom_prompts_dict = {}

        self.create_tabs()
        self.dark_mode_var.set(self.appearance == "Dark")

    # ---- Icon ------------------------------------------------------------ #
    def _set_icon(self):
        ico_path = APP_DIR / "book_to_script.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            hicon = ctypes.windll.user32.LoadImageW(
                0, str(ico_path), 1, 0, 0, 0x0010)
            if hicon:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
        except Exception:
            pass

    # ---- Appearance ----------------------------------------------------- #
    def toggle_appearance(self):
        mode = "Dark" if self.dark_mode_var.get() else "Light"
        ctk.set_appearance_mode(mode)
        self.update_idletasks()

    # ---- Tabs ----------------------------------------------------------- #
    def create_tabs(self):
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(top, text="Appearance", anchor="e").pack(side="left", padx=5, pady=5)
        ctk.CTkSwitch(top, text="Dark mode", variable=self.dark_mode_var,
                      onvalue=True, offvalue=False, command=self.toggle_appearance).pack(
                      side="right", padx=5, pady=5)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.t1 = self.tabview.add("1 · Script")
        self.build_tab1()

        self.t2 = self.tabview.add("2 · Storyboard")
        self.build_tab2()

        self.t3 = self.tabview.add("3 · Prompt Library")
        self.build_tab3()

        self.t4 = self.tabview.add("4 · Scene Canvas")
        self.build_tab4()

        self.t5 = self.tabview.add("5 · Character Sheet")
        self.build_tab5()

    def build_tab1(self):
        p = ctk.CTkScrollableFrame(self.t1, label_text="Script")
        p.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        ctk.CTkLabel(p, text="Model (name loaded in your local server, e.g. llama3.2, qwen2.5)").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.model_var = ctk.StringVar(value=self.model)
        ctk.CTkEntry(p, textvariable=self.model_var, width=340).grid(
            row=0, column=1, columnspan=4, sticky="we", padx=5, pady=5)

        ctk.CTkLabel(p, text="Prompt file (.md) - optional. If set, this file's contents are sent to the AI as the instruction instead of the built-in prompt.",
                     padx=5, pady=5).grid(row=1, column=0, sticky="w")
        self.prompt_path_var = ctk.StringVar(value="")
        ctk.CTkEntry(p, textvariable=self.prompt_path_var, width=340).grid(
            row=1, column=1, columnspan=4, sticky="we", padx=5, pady=5)
        ctk.CTkButton(p, text="Browse…", width=80, height=26,
                      command=self.browse_prompt_file).grid(
            row=1, column=5, sticky="e", padx=5, pady=5)

        ctk.CTkLabel(p, text="Local AI").grid(row=2, column=0, columnspan=6,
                                              sticky="w", padx=5, pady=(10, 0))
        self.local_ai_var = ctk.BooleanVar(value=self.local_ai)
        ctk.CTkCheckBox(p, text="Use local AI server", variable=self.local_ai_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=5, pady=4)
        self.base_url_var = ctk.StringVar(value=self.base_url)
        ctk.CTkLabel(p, text="Base URL (e.g. http://127.0.0.1:1235/v1)",
                     text_color=("gray", "gray80")).grid(row=3, column=2, sticky="w", padx=5, pady=4)
        self.base_url_entry = ctk.CTkEntry(p, textvariable=self.base_url_var, width=320)
        self.base_url_entry.grid(row=3, column=3, columnspan=3, sticky="we", padx=5, pady=4)
        ctk.CTkLabel(p, text="Checked = uses this local endpoint.",
                     text_color=("gray", "gray80")).grid(row=4, column=0, columnspan=6,
                                                        sticky="w", padx=5, pady=2)

        ctk.CTkLabel(p, text="Paste your book text here, then press Enter").grid(
            row=4, column=0, columnspan=6, sticky="w", padx=5, pady=(10, 0))
        self.input_text = ctk.CTkTextbox(p, height=120)
        self.input_text.grid(row=5, column=0, columnspan=6, sticky="nsew", padx=10, pady=5)
        self.input_text.insert("end", "Paste a book chapter or prose text here…")
        self.input_text.tag_config("sel", background="#f0c040")
        self.input_text.bind("<Return>", lambda e: self.on_generate())

        btn_frame = ctk.CTkFrame(p)
        btn_frame.grid(row=6, column=0, columnspan=6, sticky="we", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="Generate script", height=34, width=160,
                      command=self.on_generate).grid(row=0, column=0, sticky="ew", padx=5, pady=3)
        ctk.CTkButton(btn_frame, text="Clear", height=34, width=80,
                      command=lambda: self.input_text.delete("1.0", "end")).grid(
            row=0, column=1, sticky="e", padx=5, pady=3)

        ctk.CTkLabel(p, text="AI Output").grid(row=7, column=0, columnspan=6, sticky="w",
                                               padx=5, pady=(10, 0))
        self.output_text = ctk.CTkTextbox(p, height=180)
        self.output_text.grid(row=8, column=0, columnspan=6, sticky="nsew", padx=10, pady=5)
        self.output_text.insert("end", "Click Generate…")

        ctk.CTkLabel(p, text="Image engine for image prompts").grid(
            row=9, column=0, columnspan=6, sticky="w", padx=5, pady=(10, 0))
        self.image_var = ctk.StringVar(value=IMAGE_ENGINES[0])
        self.image_menu = ctk.CTkOptionMenu(p, variable=self.image_var,
                                            values=IMAGE_ENGINES, width=220)
        self.image_menu.grid(row=9, column=1, columnspan=5, sticky="w", padx=5, pady=3)

        ctk.CTkLabel(p, text="Beats (edit or clear — these drive the video plan)").grid(
            row=10, column=0, columnspan=6, sticky="w", padx=5, pady=(10, 0))
        self.beats = {}
        beats_frame = ctk.CTkFrame(p)
        beats_frame.grid(row=11, column=0, columnspan=6, sticky="nsew", padx=10, pady=5)
        for b in range(1, NUM_BEATS + 1):
            ctk.CTkLabel(beats_frame, text=f"Beat {b}:", anchor="e", width=90).grid(
                row=b - 1, column=0, sticky="e", padx=4, pady=3)
            self.beats[b] = ctk.CTkTextbox(beats_frame, height=40, width=500)
            self.beats[b].grid(row=b - 1, column=1, sticky="ew", padx=4, pady=3)

        foot = ctk.CTkFrame(p)
        foot.grid(row=12, column=0, columnspan=6, sticky="we", padx=10, pady=8)
        ctk.CTkButton(foot, text="Save script to file", width=160,
                      command=self.save_script).grid(row=0, column=0, sticky="ew", padx=5, pady=3)
        ctk.CTkButton(foot, text="Copy to clipboard", width=150,
                      command=self.copy_output).grid(row=0, column=1, sticky="e", padx=5, pady=3)

    # ---- Generate ------------------------------------------------------- #
    def on_generate(self, event=None):
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Paste some text first.")
            return
        if not self.local_ai:
            messagebox.showerror("Local AI", "Enable 'Use local AI server' before generating.")
            return
        if not self.base_url:
            messagebox.showerror("Local AI", "Set the local base URL before generating.")
            return
        self.run_generate(text)

    def run_generate(self, text):
        self.output_text.insert("end", "⏳ Generating…")
        self.output_text.see("end")
        self.input_text.configure(state="disabled")
        threading.Thread(target=self.do_generate, args=(text,), daemon=True).start()

    def do_generate(self, text):
        try:
            raw = call_ai(self.base_url, self.model, text,
                          custom_prompt=self._prompt_text())
        except requests.RequestException as e:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("end", f"Network error: {e}\n\nCheck your local server is running and reachable at {self.base_url}.")
            self.finish_generate()
            return
        except Exception as e:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("end", f"AI error: {e}")
            self.finish_generate()
            return

        sections = parse_sections(raw)
        blocks = []
        for s in SECTIONS:
            if sections[s]:
                blocks.append(f"# {s}\n\n{sections[s]}")
        self.output_text.delete("1.0", "end")
        if blocks:
            self.output_text.insert("end", "\n\n---\n\n".join(blocks) + "\n")
        else:
            cleaned = clean_screenplay_output(raw)
            self.output_text.insert("end", cleaned)

        beats = parse_beats(raw)
        for b in range(1, NUM_BEATS + 1):
            if b <= len(beats):
                self.beats[b].delete("1.0", "end")
                self.beats[b].insert("end", beats[b - 1])

        self.finish_generate()

    def finish_generate(self):
        self.input_text.configure(state="normal")
        self.model_var.set(self.model)

    # ---- Prompt source -------------------------------------------------- #
    def browse_prompt_file(self):
        path = filedialog.askopenfilename(title="Select the prompt file (.md)",
                                          filetypes=[("Markdown / Text", "*.md *.markdown *.txt")])
        if path:
            self.prompt_path_var.set(path)
            self.prompt_path = path

    def _prompt_text(self):
        path = self.prompt_path.strip()
        if path and Path(path).exists():
            try:
                return Path(path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
        if SCRIPT_WRITER_PROMPT_PATH.exists():
            try:
                return SCRIPT_WRITER_PROMPT_PATH.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
        return SYSTEM_PROMPT

    # ---- Save / copy ---------------------------------------------------- #
    def save_script(self):
        out = self.output_text.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            initialfile="script", filetypes=[("Text", "*.txt")])
        if path:
            Path(path).write_text(out, encoding="utf-8")
            messagebox.showinfo("Saved", f"Script saved to\n{path}")

    def copy_output(self):
        self.output_text.clipboard_clear()
        self.output_text.clipboard_append(self.output_text.get("1.0", "end"))

    # ---- Tab 2 ---------------------------------------------------------- #
    def build_tab2(self):
        p = ctk.CTkScrollableFrame(self.t2, label_text="Storyboard")
        p.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        row = 0
        ctk.CTkLabel(p, text="Main text file").grid(row=row, column=0, sticky="w", padx=5, pady=8)
        self.t2_text_var = ctk.StringVar(value="")
        ctk.CTkEntry(p, textvariable=self.t2_text_var, width=420).grid(
            row=row, column=1, sticky="ew", padx=5, pady=8)
        ctk.CTkButton(p, text="Browse…", width=90, height=26,
                   command=self.browse_t2_text).grid(row=row, column=2, sticky="e", padx=5, pady=8)

        self.t2_img = {}
        for i in range(1, 4):
            ctk.CTkLabel(p, text=f"Picture {i}").grid(row=row + i, column=0, sticky="w", padx=5, pady=6)
            self.t2_img[i] = ctk.StringVar(value="")
            ctk.CTkEntry(p, textvariable=self.t2_img[i], width=420).grid(
                row=row + i, column=1, sticky="ew", padx=5, pady=6)
            ctk.CTkButton(p, text="Browse…", width=90, height=26,
                       command=lambda idx=i: self.browse_image(idx)).grid(
                row=row + i, column=2, sticky="e", padx=5, pady=6)

        ctk.CTkLabel(p, text="Environment picture").grid(row=row + 4, column=0, sticky="w", padx=5, pady=6)
        self.t2_env_var = ctk.StringVar(value="")
        ctk.CTkEntry(p, textvariable=self.t2_env_var, width=420).grid(
            row=row + 4, column=1, sticky="ew", padx=5, pady=6)
        ctk.CTkButton(p, text="Browse…", width=90, height=26,
                   command=lambda: self.browse_image_env()).grid(
            row=row + 4, column=2, sticky="e", padx=5, pady=6)

        ctk.CTkLabel(p, text="Video model").grid(row=row + 5, column=0, sticky="w", padx=5, pady=8)
        self.video_var = ctk.StringVar(value=VIDEO_MODELS[0])
        ctk.CTkOptionMenu(p, variable=self.video_var, values=VIDEO_MODELS, width=200).grid(
            row=row + 5, column=1, sticky="w", padx=5, pady=8)

        ctk.CTkLabel(p, text="Runtime").grid(row=row + 6, column=0, sticky="w", padx=5, pady=8)
        self.runtime_var = ctk.StringVar(value=RUNTIME_PRESETS[1])
        ctk.CTkOptionMenu(p, variable=self.runtime_var, values=RUNTIME_PRESETS, width=200).grid(
            row=row + 6, column=1, sticky="w", padx=5, pady=8)

        ctk.CTkLabel(p, text="Storyboard summary").grid(row=row + 7, column=0, columnspan=3,
                                                        sticky="w", padx=5, pady=(12, 0))
        self.storyboard_text = ctk.CTkTextbox(p, height=200)
        self.storyboard_text.grid(row=row + 8, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
        self.storyboard_text.insert("end", "Your assembled storyboard will appear here.")

        foot = ctk.CTkFrame(p)
        foot.grid(row=row + 9, column=0, columnspan=3, sticky="we", padx=10, pady=8)
        ctk.CTkButton(foot, text="Assemble storyboard", width=170,
                      command=self.assemble_storyboard).grid(row=0, column=0, sticky="ew", padx=5, pady=3)
        ctk.CTkButton(foot, text="Save storyboard", width=150,
                      command=self.save_storyboard).grid(row=0, column=1, sticky="e", padx=5, pady=3)

    # ---- Prompt Library ------------------------------------------------ #
    def build_tab3(self):
        p = ctk.CTkFrame(self.t3)
        p.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        ctk.CTkLabel(p, text="Presets").pack(anchor="w", padx=5, pady=(10, 0))
        self.preset_list = Listbox(p, height=12, font=("Segoe UI", 10))
        preset_scroll = Scrollbar(p, command=self.preset_list.yview)
        self.preset_list.configure(yscrollcommand=preset_scroll.set)
        self.preset_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        preset_scroll.pack(side="right", fill="y", padx=5, pady=5)
        for name, _ in PRESETS:
            self.preset_list.insert("end", name)
        self.preset_list.bind("<Enter>", self._list_enter)
        self.preset_list.bind("<B1-Motion>", self._auto_scroll)

        btn_row = ctk.CTkFrame(p)
        btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="Load into editor", width=150,
                      command=self.load_into_editor).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="Use this prompt", width=150,
                      command=self.use_prompt).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="Save as custom", width=150,
                      command=self.save_custom).pack(side="left", padx=5, pady=5)

        ctk.CTkLabel(p, text="My custom prompts").pack(anchor="w", padx=5, pady=(15, 0))
        self.custom_list = Listbox(p, height=8, font=("Segoe UI", 10))
        custom_scroll = Scrollbar(p, command=self.custom_list.yview)
        self.custom_list.configure(yscrollcommand=custom_scroll.set)
        self.custom_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        custom_scroll.pack(side="right", fill="y", padx=5, pady=5)
        for name in self.custom_prompts:
            self.custom_list.insert("end", name)
        self.custom_list.bind("<Enter>", self._list_enter)
        self.custom_list.bind("<B1-Motion>", self._auto_scroll)

        ctk.CTkLabel(p, text="Current prompt (edit freely, then Use this prompt to apply it to Tab 1)").pack(
            anchor="w", padx=5, pady=(15, 0))
        self.prompt_text = ctk.CTkTextbox(p, height=200)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        self._refresh_lists()

    # ---- Scene Canvas (Tab 4) ------------------------------------------ #
    def build_tab4(self):
        p = ctk.CTkScrollableFrame(self.t4, label_text="Scene Canvas")
        p.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(p, text="Scene Canvas is a browser-based scene planner (a Pureref-style board for scenes).",
                     justify="left", wraplength=900).pack(anchor="w", padx=5, pady=(0, 10))
        ctk.CTkLabel(p, text="It needs a browser engine to run. Click the button to open it in your default browser.",
                     justify="left", wraplength=900, text_color=("gray", "gray80")).pack(anchor="w", padx=5, pady=(0, 10))

        btn_frame = ctk.CTkFrame(p)
        btn_frame.pack(fill="x", padx=5, pady=10)
        ctk.CTkButton(btn_frame, text="Launch Scene Canvas", height=38, width=260,
                      command=self.launch_scene_canvas).grid(row=0, column=0, sticky="ew", padx=5, pady=3)

        ctk.CTkLabel(p, text="Drag reference images onto the canvas, name them, connect them, then generate a video prompt. Each scene is one saveable sheet (saved in your browser).",
                     justify="left", wraplength=900, text_color=("gray", "gray80")).pack(anchor="w", padx=5, pady=(0, 10))

    def launch_scene_canvas(self):
        candidates = [
            APP_DIR / "SceneCanvas" / "SceneCanvas.html",
            APP_DIR.parent / "SceneCanvas" / "SceneCanvas.html",
            Path(r"C:\book to script\SceneCanvas\SceneCanvas.html"),
        ]
        path = None
        for c in candidates:
            if c.exists():
                path = c
                break
        if not path:
            messagebox.showerror("Scene Canvas",
                f"SceneCanvas.html not found.\nSearched:\n" +
                "\n".join(str(c) for c in candidates))
            return
        try:
            import webbrowser
            webbrowser.open("file:///" + str(path).replace("\\", "/"))
        except Exception as e:
            messagebox.showerror("Scene Canvas", f"Could not open Scene Canvas:\n{e}")

    # ---- Tab 5: Character Sheet Creator --------------------------------- #
    def build_tab5(self):
        p = ctk.CTkFrame(self.t5)
        p.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        left = ctk.CTkFrame(p, width=280)
        left.pack(side="left", fill="y", padx=(0, 5), pady=5)

        ctk.CTkLabel(left, text="VAULT FOLDER", font=("", 12, "bold")).pack(
            anchor="w", padx=5, pady=(10, 0))
        ctk.CTkButton(left, text="Browse Folder...", width=240, height=30,
                      command=self.browse_vault_folder).pack(padx=5, pady=5)

        self.t5_vault_path_var = ctk.StringVar(value="No folder selected")
        ctk.CTkLabel(left, textvariable=self.t5_vault_path_var,
                     text_color=("gray", "gray80"), wraplength=250,
                     justify="left").pack(anchor="w", padx=5, pady=(0, 5))

        ctk.CTkLabel(left, text="FILES (.md)", font=("", 11, "bold")).pack(
            anchor="w", padx=5, pady=(10, 0))

        list_frame = ctk.CTkFrame(left)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.t5_file_list = Listbox(list_frame, height=14, font=("Segoe UI", 10),
                                    selectmode="extended")
        file_scroll = Scrollbar(list_frame, command=self.t5_file_list.yview)
        self.t5_file_list.configure(yscrollcommand=file_scroll.set)
        self.t5_file_list.pack(side="left", fill="both", expand=True)
        file_scroll.pack(side="right", fill="y")

        btn_row = ctk.CTkFrame(left)
        btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="Select All", width=115, height=28,
                      command=self.t5_select_all).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Deselect All", width=115, height=28,
                      command=self.t5_deselect_all).pack(side="left", padx=2)

        self.t5_files_selected_var = ctk.StringVar(value="Files selected: 0")
        ctk.CTkLabel(left, textvariable=self.t5_files_selected_var,
                     text_color=("gray", "gray80")).pack(anchor="w", padx=5, pady=(0, 5))

        self.t5_file_list.bind("<<ListboxSelect>>", self.t5_on_file_select)

        right = ctk.CTkFrame(p)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=5)

        ctk.CTkLabel(right, text="CHARACTER SHEET", font=("", 12, "bold")).pack(
            anchor="w", padx=5, pady=(10, 0))

        name_frame = ctk.CTkFrame(right)
        name_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(name_frame, text="Character Name:", width=120).pack(side="left", padx=5)
        self.t5_char_name_var = ctk.StringVar(value="")
        ctk.CTkEntry(name_frame, textvariable=self.t5_char_name_var, width=300).pack(
            side="left", padx=5, fill="x", expand=True)

        gen_frame = ctk.CTkFrame(right)
        gen_frame.pack(fill="x", padx=5, pady=5)
        self.t5_generate_btn = ctk.CTkButton(gen_frame, text="Generate Character Sheet",
                                              height=36, width=220,
                                              command=self.t5_generate)
        self.t5_generate_btn.pack(side="left", padx=5)
        self.t5_status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(gen_frame, textvariable=self.t5_status_var,
                     text_color=("gray", "gray80")).pack(side="left", padx=10)

        ctk.CTkLabel(right, text="Generated Character Sheet").pack(
            anchor="w", padx=5, pady=(10, 0))
        self.t5_output = ctk.CTkTextbox(right, height=300)
        self.t5_output.pack(fill="both", expand=True, padx=5, pady=5)
        self.t5_output.insert("end", "Select files from the vault, enter a character name, and click Generate.")

        foot = ctk.CTkFrame(right)
        foot.pack(fill="x", padx=5, pady=8)
        ctk.CTkButton(foot, text="Save As...", width=140, height=32,
                      command=self.t5_save).pack(side="left", padx=5)
        ctk.CTkButton(foot, text="Copy to Clipboard", width=160, height=32,
                      command=self.t5_copy).pack(side="left", padx=5)
        ctk.CTkButton(foot, text="Load Existing...", width=150, height=32,
                      command=self.t5_load).pack(side="left", padx=5)
        ctk.CTkButton(foot, text="Clear", width=80, height=32,
                      command=self.t5_clear).pack(side="right", padx=5)

        self.t5_vault_folder = ""
        self.t5_vault_files = []

    # ---- Tab 5 helpers -------------------------------------------------- #
    def browse_vault_folder(self):
        folder = filedialog.askdirectory(title="Select Obsidian vault folder",
                                         initialdir=DEFAULT_VAULT_PATH)
        if folder:
            self.t5_vault_folder = folder
            short = folder if len(folder) < 40 else "..." + folder[-37:]
            self.t5_vault_path_var.set(short)
            self.t5_populate_files()

    def t5_populate_files(self):
        self.t5_file_list.delete(0, "end")
        self.t5_vault_files = []
        if not self.t5_vault_folder:
            return
        vault_path = Path(self.t5_vault_folder)
        if not vault_path.exists():
            return
        for f in sorted(vault_path.rglob("*.md")):
            rel = f.relative_to(vault_path)
            self.t5_vault_files.append(str(f))
            self.t5_file_list.insert("end", str(rel))
        self.t5_files_selected_var.set(f"Files: {len(self.t5_vault_files)}")

    def t5_select_all(self):
        self.t5_file_list.select_set(0, "end")
        self.t5_on_file_select()

    def t5_deselect_all(self):
        self.t5_file_list.selection_clear(0, "end")
        self.t5_on_file_select()

    def t5_on_file_select(self, event=None):
        sel = self.t5_file_list.curselection()
        self.t5_files_selected_var.set(f"Files selected: {len(sel)}")

    def t5_get_selected_files(self):
        indices = self.t5_file_list.curselection()
        return [self.t5_vault_files[i] for i in indices if i < len(self.t5_vault_files)]

    def t5_generate(self):
        char_name = self.t5_char_name_var.get().strip()
        if not char_name:
            messagebox.showwarning("Missing Name", "Enter a character name first.")
            return
        selected = self.t5_get_selected_files()
        if not selected:
            messagebox.showwarning("No Files", "Select at least one file from the vault.")
            return
        if not self.local_ai:
            messagebox.showerror("Local AI", "Enable 'Use local AI server' in Tab 1 first.")
            return
        if not self.base_url:
            messagebox.showerror("Local AI", "Set the local base URL in Tab 1 first.")
            return
        self.t5_generate_btn.configure(state="disabled")
        self.t5_status_var.set("Reading files...")
        threading.Thread(target=self.t5_do_generate, args=(char_name, selected),
                         daemon=True).start()

    def t5_do_generate(self, char_name, file_paths):
        try:
            combined_text = ""
            for fp in file_paths:
                p = Path(fp)
                combined_text += f"\n\n--- FILE: {p.name} ---\n\n"
                combined_text += p.read_text(encoding="utf-8", errors="replace")

            prompt_text = self._character_sheet_prompt()
            user_msg = (f"Character Name: {char_name}\n\n"
                        f"Source Material:\n{combined_text}")

            self.after(0, lambda: self.t5_status_var.set("Generating character sheet..."))
            raw = call_ai(self.base_url, self.model, user_msg, timeout=1400,
                          custom_prompt=prompt_text)
        except requests.RequestException as e:
            self.after(0, lambda: self.t5_output.delete("1.0", "end"))
            self.after(0, lambda: self.t5_output.insert("end",
                f"Network error: {e}\n\nCheck your local server at {self.base_url}."))
            self.after(0, self.t5_finish_generate)
            return
        except Exception as e:
            self.after(0, lambda: self.t5_output.delete("1.0", "end"))
            self.after(0, lambda: self.t5_output.insert("end", f"AI error: {e}"))
            self.after(0, self.t5_finish_generate)
            return

        self.after(0, lambda: self.t5_output.delete("1.0", "end"))
        self.after(0, lambda: self.t5_output.insert("end", raw))
        self.after(0, lambda: self.t5_status_var.set(
            f"Generated for '{char_name}' ({len(file_paths)} files)"))
        self.after(0, self.t5_finish_generate)

    def t5_finish_generate(self):
        self.t5_generate_btn.configure(state="normal")

    def _character_sheet_prompt(self):
        if CHARACTER_SHEET_PROMPT_PATH.exists():
            try:
                return CHARACTER_SHEET_PROMPT_PATH.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
        return SYSTEM_PROMPT

    def t5_save(self):
        content = self.t5_output.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Empty", "Nothing to save. Generate a character sheet first.")
            return
        char_name = self.t5_char_name_var.get().strip() or "character"
        safe_name = re.sub(r'[^\w\s-]', '', char_name).strip().replace(' ', '_')
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            initialfile=f"{safe_name}_sheet",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if path:
            Path(path).write_text(content, encoding="utf-8")
            messagebox.showinfo("Saved", f"Character sheet saved to\n{path}")

    def t5_copy(self):
        self.t5_output.clipboard_clear()
        self.t5_output.clipboard_append(self.t5_output.get("1.0", "end"))

    def t5_load(self):
        path = filedialog.askopenfilename(
            title="Load existing character sheet",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt")])
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8", errors="replace")
                self.t5_output.delete("1.0", "end")
                self.t5_output.insert("end", content)
                self.t5_status_var.set(f"Loaded: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Read Error", f"Could not read file:\n{e}")

    def t5_clear(self):
        self.t5_output.delete("1.0", "end")
        self.t5_output.insert("end", "Select files from the vault, enter a character name, and click Generate.")
        self.t5_status_var.set("Ready")

    def _list_enter(self, event):
        event.widget.focus()

    def _auto_scroll(self, event):
        w = event.widget
        first = w.viewregion()[1]
        last = first + w.height()
        if event.y < first:
            w.yview(0.5 * (event.y / first))
        elif event.y > last:
            w.yview(0.5 * ((event.y - last) / (last - first)))

    def _load_custom_prompts(self):
        try:
            data = json.loads(CUSTOM_PATH.read_text(encoding="utf-8"))
            return [d["name"] for d in data if isinstance(d, dict) and d.get("name")]
        except Exception:
            return []

    def _save_custom_prompts(self):
        data = [{"name": n, "prompt": self.custom_prompts_dict.get(n, "")}
                for n in self.custom_prompts]
        CUSTOM_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _refresh_lists(self):
        self.preset_list.delete(0, "end")
        for name, _ in PRESETS:
            self.preset_list.insert("end", name)
        self.custom_list.delete(0, "end")
        for name in self.custom_prompts:
            self.custom_list.insert("end", name)

    def load_into_editor(self):
        idx = self.preset_list.curselection()
        if not idx:
            return
        _, prompt = PRESETS[idx[0]]
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("end", prompt)

    def use_prompt(self):
        text = self.prompt_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Load or write a prompt first.")
            return
        self.custom_prompt = text
        self.tabview.select(self.t1)
        messagebox.showinfo("Ready", "Prompt applied. Go to Tab 1 and press Generate.")

    def save_custom(self):
        text = self.prompt_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Write a prompt first.")
            return
        name = messagebox.askstring("Save custom prompt", "Name this prompt:", initial="My prompt")
        if not name:
            return
        if name in self.custom_prompts:
            messagebox.showinfo("Exists", "A prompt with that name already exists.")
            return
        self.custom_prompts.append(name)
        self.custom_prompts_dict[name] = text
        self._save_custom_prompts()
        self._refresh_lists()
        messagebox.showinfo("Saved", f"'{name}' saved to Prompt Library.")

    def browse_t2_text(self):
        path = filedialog.askopenfilename(title="Select the script text file",
                                          filetypes=[("Text", "*.txt *.md")])
        if path:
            try:
                self.t2_text_var.set(path)
                self.t2_text_status.set(Path(path).read_text(encoding="utf-8", errors="replace"))
            except Exception:
                messagebox.showerror("Read error", "Could not read that file.")

    def browse_image(self, idx):
        path = filedialog.askopenfilename(title=f"Select Picture {idx}")
        if path:
            self.t2_img[idx].set(path)

    def browse_image_env(self):
        path = filedialog.askopenfilename(title="Select environment picture")
        if path:
            self.t2_env_var.set(path)

    def _linked_files(self):
        files = []
        for i in (1, 2, 3):
            v = self.t2_img[i].get().strip()
            if v and Path(v).exists():
                files.append(v)
        env = self.t2_env_var.get().strip()
        if env and Path(env).exists():
            files.append(env)
        return files

    def assemble_storyboard(self):
        text = self.t2_text_var.get().strip()
        files = self._linked_files()
        if not text:
            messagebox.showwarning("Nothing to do", "Link a text file first (top of Tab 2).")
            return
        if not files:
            messagebox.showwarning("No images", "Link at least one picture or environment image.")
            return
        self.storyboard_text.insert("end",
            f"Video model: {self.video_var.get()}\n"
            f"Runtime: {self.runtime_var.get()}\n"
            f"Linked files ({len(files)}):\n  " + "\n  ".join(files) + "\n")
        messagebox.showinfo("Ready", "Storyboard assembled. Click Save storyboard to export.")

    def save_storyboard(self):
        out = self.storyboard_text.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            initialfile="storyboard", filetypes=[("Text", "*.txt")])
        if path:
            Path(path).write_text(out, encoding="utf-8")
            messagebox.showinfo("Saved", f"Storyboard saved to\n{path}")


if __name__ == "__main__":
    app = BookToScriptApp()
    app.mainloop()
