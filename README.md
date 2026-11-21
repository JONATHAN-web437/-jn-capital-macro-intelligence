# JN Capital Macro Intelligence — Starter V1

A local Streamlit research-dashboard foundation using free data sources.

## Setup (Windows / VS Code)

1. Extract this project folder.
2. Open the folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:

   `py -m venv .venv`

5. Activate it:

   `.venv\\Scripts\\Activate.ps1`

   If PowerShell blocks activation, use Command Prompt terminal and run:
   `.venv\\Scripts\\activate.bat`

6. Install dependencies:

   `python -m pip install -r requirements.txt`

7. Copy `.env.example` to `.env`, and enter your FRED API key.
8. Start the app:

   `streamlit run app.py`

## FRED API key
Register for a free key through the official FRED API website. Never share or commit your key.

## Notes
- This is a starter, not an investment signal or finished terminal.
- FRED series are not necessarily real-time and publication dates vary.
- Later modules will add source-specific adapters, history, event/release records, charts, positioning, correlation studies and research reports.
