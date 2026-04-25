#!/usr/bin/env python3
"""
Simple launcher for Nova Assistant = TEST
"""

import subprocess
import sys
import os
"""
Nova Assistant - Configuration & Setup Notes
=============================================

LAUNCH & INTERFACE
------------------
- This file launches nova_assistant_v1.py
- Web interface supported - accessible from mobile devices on the same network
- Press "new chat" to reset conversation history; otherwise, session history persists across restarts

MODEL SELECTION
---------------
- Cloud models (OpenRouter) - Recommended when internet is available
- Offline mode (Ollama) - Requires compatible graphics card and pre-downloaded models
- If no Ollama models are detected, system automatically falls back to OpenRouter

TEXT RENDERING
--------------
- LaTeX window disabled by default - uses MathJax in browser for better presentation
- MathJax requires internet connection to render properly

SYSTEM REQUIREMENTS
-------------------
- Windows only (Linux support planned but not tested)
- PyCharm (Free Edition) - Development environment used
- Visual Studio Desktop C++ Tools - Required for first-time PyCharm setup on Windows

SPEECH RECOGNITION (faster-whisper)
-----------------------------------
- Language: English (can be configured for other languages)
- CUDA support: Uses GPU if available; falls back to CPU if not (slower)
- Input methods: Tkinter console, web interface, or mobile device

TEXT-TO-SPEECH
--------------
- Web browser: Microsoft Edge recommended for web speech synthesis
- Desktop: SAPI5 or Edge voices available
- Tablet: Edge browser only
- Note: Disable console TTS when using web Edge voices to avoid double playback

WEB SECURITY
------------
- Run `Certificate_Generate.py` first to generate SSL certificates
- Script auto-detects your IP address and creates certificates for HTTPS connections

DEPENDENCIES
------------
See README.md for full installation instructions

.env File
------------
Fill that out, includes your openrouter and Brave api keys. Brave is free for 2000 searches.

"""

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the main program
    main_program = os.path.join(script_dir, "nova_assistant_v1.py")

    # Check if the main program exists
    if not os.path.exists(main_program):
        print(f"Error: {main_program} not found!")
        print(f"Make sure nova_assistant_v1.py is in the same folder as this script.")
        sys.exit(1)

    # Run the main program
    print("Starting Nova Assistant...")
    subprocess.run([sys.executable, main_program] + sys.argv[1:])