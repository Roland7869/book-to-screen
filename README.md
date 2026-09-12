<img width="1457" height="970" alt="image" src="https://github.com/user-attachments/assets/5de54781-c946-4767-a6dd-6e65b08bf5ba" />

<img width="1461" height="967" alt="image" src="https://github.com/user-attachments/assets/74018c30-554c-4c03-8df5-9a88548fc687" />

<img width="1460" height="971" alt="image" src="https://github.com/user-attachments/assets/e597a511-e55b-4221-95b0-c1465bcc5fe8" />

<img width="1462" height="972" alt="image" src="https://github.com/user-attachments/assets/53c850c2-bd03-4d15-8bf3-8d550f9f3e90" />

<img width="1992" height="1392" alt="image" src="https://github.com/user-attachments/assets/45589f33-fda4-492c-b14e-6a2f1a33a56e" />

<img width="1457" height="961" alt="image" src="https://github.com/user-attachments/assets/947fa42b-118a-4748-963f-ff98131122bd" />



# Book-to-Screen AI Production Pipeline

Turn a book chapter or prose text into an AI-assisted video-production pipeline.


Paste your text → the AI breaks it down into a structured screenplay with **character references, environments, shot direction, storyboards, narration and scene beats** → choose an **image engine** to format image prompts → edit the beats → build a storyboard.


The project is designed as a workflow for moving from written fiction toward AI-assisted visual and video production.


---


## Features


* Convert book chapters or prose into a structured screenplay
* Extract and organise:


  * Characters
  * Environments
  * Scene descriptions
  * Shot direction
  * Narration
  * Storyboards
  * Scene beats
* Format image prompts for different image-generation engines
* Edit and refine story beats before production
* Build storyboard summaries
* Manage reusable AI prompt presets
* Use a browser-based visual Scene Canvas
* Generate comprehensive character sheets
* Browse and use an Obsidian Vault as a story source
* Track character descriptions and continuity across source material
* Run against local or cloud-based OpenAI-compatible AI servers
* Includes an MCP server for integration with AI development environments


---


# Run the Application


There are two ways to run Book-to-Screen.


## Option A — Run directly with Python


This is the fastest way to try the application.


### 1. Install the dependencies


```bash
pip install -r requirements.txt
```


### 2. Start the application


Double-click:


```text
run_app.bat
```


Or run:


```bash
python book_to_script_app.py
```


---


## Option B — Build a standalone `.exe`


This creates a Windows executable that can be launched without Python being installed on the target computer.


### 1. Install PyInstaller


```bash
pip install pyinstaller
```


### 2. Build the application


Double-click:


```text
compile_exe.bat
```


### 3. Run the executable


The generated executable will be placed in the `dist` folder.


Double-click:


```text
book-to-screen.exe
```


---


# AI Provider Setup


The application communicates with **OpenAI-compatible API servers**.


Set the **Base URL** in Tab 1 to point to your AI provider.


| Provider          | Base URL                      | Notes                                        |
| ----------------- | ----------------------------- | -------------------------------------------- |
| Ollama (local)    | `http://127.0.0.1:11434/v1`   | OpenAI-compatible endpoint                   |
| LM Studio (local) | `http://127.0.0.1:1234/v1`    | Load and start a model first                 |
| OpenAI            | `https://api.openai.com/v1`   | Requires API authentication                  |
| DeepSeek          | `https://api.deepseek.com/v1` | Requires API authentication                  |
| Anthropic         | OpenAI-compatible proxy       | Requires a compatible proxy or gateway       |
| Google Gemini     | OpenAI-compatible proxy       | Requires a compatible proxy or gateway       |
| vLLM / LocalAI    | Varies                        | Any server exposing an OpenAI-compatible API |


> **Note:** The application currently communicates using the OpenAI-compatible API format. Providers that do not natively expose an OpenAI-compatible endpoint require a compatible proxy, gateway or adapter.


For cloud providers, API authentication must be configured appropriately.


Local servers such as Ollama or LM Studio can be used without sending your book material to a third-party cloud provider, depending on your local setup.


---


# First Use


1. Start your local AI server.


2. Open Book-to-Screen.


3. In **Tab 1**, make sure the Base URL points to your AI server.


   Examples:


   ```text
   Ollama:
   http://127.0.0.1:11434/v1


   LM Studio:
   http://127.0.0.1:1234/v1
   ```


4. Enter the name of your loaded model.


   Examples:


   ```text
   llama3.2
   qwen2.5
   mistral
   ```


5. Paste your book chapter or prose into the main text box.


6. Click **Generate Script**.


7. The AI output is processed into structured scenes.


8. Review and edit the generated **Beats**.


9. Switch to **Tab 2** to prepare and assemble your storyboard.


---


# What Each Tab Does


## Tab 1 · Script


The main adaptation and screenplay-generation workspace.


Features include:


* **Model**
  Enter the name of the model running on your AI server.


* **Prompt File (`.md`)**
  Load a custom Markdown prompt file. Its contents are used as the AI instruction instead of the default screenplay-generation prompt.


* **Local AI / Base URL**
  Configure the OpenAI-compatible AI server used by the application.


* **Text Input**
  Paste book chapters, prose or other source material.


* **Screenplay Output**
  Generated material is structured into scenes containing information such as:


  * Characters
  * Environments
  * Scene action
  * Shot direction
  * Storyboard information
  * Narration


* **Image Engine**
  Select an image-generation engine to format image prompts.


  Current options include:


  * Z-Image Turbo
  * LTX
  * SEEDANCE 2.5
  * Midjourney
  * Flux
  * DALL·E 3


* **Beats**
  Editable story beats automatically generated from the scene breakdown.


* **Export Tools**


  * Save script
  * Copy output to clipboard


---


## Tab 2 · Storyboard


The storyboard preparation workspace.


You can:


* Link the main text file
* Add reference images
* Add an environment image
* Select a video model
* Select a runtime
* Assemble the storyboard
* Save the storyboard output


Supported video-model options currently include:


* LTX
* SEEDANCE 2.5
* Runway
* Kling
* Hailuo
* Sora


The storyboard workflow is intended to organise scene information before moving into AI video generation.


---


## Tab 3 · Prompt Library


Browse and manage reusable prompt presets.


You can:


* Browse existing prompts
* Load prompt presets
* Create custom prompts
* Manage reusable prompt workflows


---


## Tab 4 · Scene Canvas


Launches the bundled browser-based Scene Canvas.


The Scene Canvas works as a visual reference board for planning scenes.


You can:


* Add reference images
* Name visual references
* Connect related elements
* Organise scene references
* Build visual relationships between characters and environments
* Generate a video prompt for a scene
* Save individual scene sheets


It can be used as a lightweight, browser-based alternative to a Pureref-style scene board.


---


## Tab 5 · Character Sheet Creator


The Character Sheet Creator is designed to build detailed, reusable character references from source material.


Features include:


* Browse an Obsidian Vault
* Select book or story files
* Enter a character name
* Analyse source material using AI
* Generate a structured character sheet


Character sheets can include:


* Physical description
* Age
* Height
* Body type and figure
* Skin and hair description
* Clothing and outfit continuity
* Psychological traits
* Voice and speech characteristics
* Character behaviour
* Confirmed canonical information
* Strongly implied information
* Unknown information
* User-defined production information
* Continuity tracking
* Reusable image and video prompt blocks


The system is intended to distinguish between information directly supported by the source material and information that has been inferred or added for production purposes.


---


# Project Structure


```text
book-to-screen/
│
├── book_to_script_app.py
│   Main CustomTkinter application
│
├── character_sheet_prompt.md
│   Character Sheet Creator system prompt
│
├── script_writer_prompt.md
│   Screenplay and story adaptation system prompt
│
├── book_to_script.ico
│   Application icon
│
├── book_to_script_app.spec
│   PyInstaller configuration
│
├── compile_exe.bat
│   Windows executable build script
│
├── run_app.bat
│   Application launch script
│
├── requirements.txt
│   Python dependencies
│
├── config.example.json
│   Example application configuration
│
├── SceneCanvas/
│   │
│   └── SceneCanvas.html
│       Browser-based visual scene planner
│
├── book_to_script_mcp/
│   │
│   ├── server.py
│   │   MCP server
│   │
│   └── README.md
│       MCP integration information
│
├── .gitignore
│   Git ignore rules
│
└── README.md
```


---


# Project Philosophy


Book-to-Screen is designed around the idea that AI-generated visual production benefits from **structured continuity**.


Generating an individual image or video clip is relatively easy.


Maintaining consistency across an entire story is much more difficult.


The project therefore focuses on building structured information that can move through the production pipeline:


```text
Book / Prose
      ↓
Story Analysis
      ↓
Screenplay
      ↓
Characters + Continuity
      ↓
Environments
      ↓
Scene Beats
      ↓
Image Prompts
      ↓
Visual References
      ↓
Storyboard
      ↓
Video Production
```


The Character Sheet Creator and Obsidian Vault workflow are intended to help maintain persistent story and character information across a larger project.


---


# AI-Assisted Development


This project was developed using AI-assisted programming.


The project concept, workflow design, feature requirements and iterative development direction were created and refined by the project author, while AI tools assisted with implementation and development.


---


# Project Status


**Early Public Release / Work in Progress**


Book-to-Screen is actively evolving.


The project is being developed as an experimental AI-assisted production workflow, and features, prompts, file formats and architecture may change as the system develops.


Feedback, ideas and contributions are welcome.


---


# License


* **MIT License** — simple and permissive
* **Apache License 2.0** — permissive with additional patent protections
* **GPLv3** — requires derivative open-source projects to remain open source



