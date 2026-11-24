# TIA → moneo Converter (v3.0)

Graphical user interface for converting TIA Portal data block exports (XML from the
Version Control Interface) into the moneo import file (JSON). Successor of `TIAExportv2.exe`.

**The processing is unchanged:** `core.py` is bytecode-identical to the original, and the saved
JSON is written byte for byte exactly as produced by the original function.

## Usage
1. Start `TIA2moneo.exe`.
2. Drag XML file(s) into the window or click "Select XML file…".
3. Review signals and skipped variables in the preview.
4. Click "Save as JSON…" or, with several files, "Save all…".

Requirement: Windows 10/11 with Microsoft Edge WebView2 Runtime (pre-installed on Windows 11).

## Structure
| Path | Purpose |
|---|---|
| `core.py` | Conversion, taken 1:1 from the original – **do not modify** |
| `service.py` | Calls `core`, provides preview + diagnostics (skipped variables), saves |
| `app.py` | Window (pywebview / Edge WebView2), file dialogs, drag & drop |
| `ui/` | User interface (HTML/CSS/JS); `ui/demo.js` is for browser preview only and not bundled into the exe |
| `tests/` | Regression test against the old exe, test XML files in `tests/fixtures` |
| `legacy/TIAExportv2.exe` | Previous console version, reference for the regression test |
| `TIA2moneo.spec` | PyInstaller build configuration |

## Development
Python **3.12** is required (the old exe was built with 3.12; the regression test compares bytecode).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Run the app from source:
```powershell
.venv\Scripts\python app.py
```

Run the regression test (compares with `legacy\TIAExportv2.exe`):
```powershell
.venv\Scripts\python tests\test_regression.py
```

Build the exe (output: `dist\TIA2moneo.exe`):
```powershell
.venv\Scripts\python -m PyInstaller --noconfirm --clean TIA2moneo.spec
```

Preview the UI in a browser with demo data (no Python backend needed):
```powershell
.venv\Scripts\python -m http.server 8765 -d ui
```
then open `http://localhost:8765/index.html?demo`.

## Regression test
The test loads the original script directly from `legacy\TIAExportv2.exe`, compares the bytecode
of the conversion functions and converts every XML file in `tests\fixtures` (plus any files passed
as arguments) with both the original and the new version. All outputs must be byte-identical.

- Add real TIA exports by placing them in `tests\fixtures` or passing them as arguments:
  `.venv\Scripts\python tests\test_regression.py C:\path\to\export.xml`
- To use a different reference exe, set the environment variable `TIA2MONEO_LEGACY_EXE`.

## Notes
- The original function prints a German console message ("Konvertierung abgeschlossen!").
  It is kept on purpose to preserve bytecode identity; it is not visible in the GUI.
- Behaviour inherited from the original: every signal gets `"Unit": "K"`; arrays, UDT instances
  and types such as `Time` or `DTL` are not transferred. The GUI lists these under "Skipped".
- The last used folders are stored in `%APPDATA%\TIA2moneo\settings.json`.
