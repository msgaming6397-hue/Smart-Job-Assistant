# How to Run "Smart Job Assistant" Offline

This project is already saved in your folder: `c:\Users\moham\.gemini\antigravity\playground\inner-kepler`

Note: While the web server runs "offline" (locally on your computer), **you must have an internet connection** because the AI (Google Gemini) runs in the cloud.

### Option 1: One-Click Run (Easiest)
1. Navigate to the project folder.
2. Double-click the file named **`run_app.bat`**.
3. A black command window will open (keep it open).
4. Go to your browser and visit: `http://127.0.0.1:5000`

### Option 2: Manual Run
1. Open a terminal (PowerShell or Command Prompt).
2. Type `cd` and drag the project folder into the window to paste the path.
3. Run this command:
   ```powershell
   python app.py
   ```
4. Open `http://127.0.0.1:5000` in your browser.

### Requirements
- **Python** must be installed on your computer.
- **Internet Connection** is required for the AI to analyze resumes.
