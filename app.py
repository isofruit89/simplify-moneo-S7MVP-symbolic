"""TIA → moneo Converter - desktop UI (pywebview + HTML)."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import webview
from webview.dom import DOMEventHandler

import service

APP_TITLE = "TIA → moneo Converter"
APP_VERSION = "3.0"
SETTINGS_FILE = Path(os.environ.get("APPDATA", Path.home())) / "TIA2moneo" / "settings.json"


def resource_path(*parts: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base.joinpath(*parts))


class Settings:
    def __init__(self):
        try:
            self.data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}

    def get(self, key, default=""):
        value = self.data.get(key, default)
        return value if value and os.path.isdir(value) else default

    def set(self, key, value):
        self.data[key] = value
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass


class Api:
    def __init__(self):
        self._window = None
        self._items: dict[str, service.Conversion] = {}
        self._lock = threading.Lock()
        self._settings = Settings()

    # -- internal ---------------------------------------------------------
    def attach(self, window):
        self._window = window

    def _analyze_paths(self, paths):
        results = []
        for p in paths:
            if not str(p).lower().endswith(".xml"):
                results.append({"ok": False, "fileName": Path(p).name, "xmlPath": str(p),
                                "error": "Not an XML file."})
                continue
            try:
                conv = service.analyze(p)
            except Exception as exc:  # show the error instead of crashing
                results.append({"ok": False, "fileName": Path(p).name, "xmlPath": str(p),
                                "error": service.describe_error(exc)})
                continue
            with self._lock:
                self._items[conv.id] = conv
            results.append(conv.to_dict())
        if paths:
            self._settings.set("last_xml_dir", str(Path(paths[0]).resolve().parent))
        return results

    # -- callable from JavaScript -----------------------------------------
    def info(self):
        return {"title": APP_TITLE, "version": APP_VERSION}

    def pick_files(self):
        selected = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            directory=self._settings.get("last_xml_dir"),
            allow_multiple=True,
            file_types=("XML files (*.xml)", "All files (*.*)"),
        )
        return self._analyze_paths(list(selected or []))

    def remove(self, item_id):
        with self._lock:
            self._items.pop(item_id, None)
        return True

    def save_one(self, item_id):
        conv = self._items.get(item_id)
        if conv is None:
            return {"ok": False, "error": "Entry no longer available."}
        start_dir = self._settings.get("last_json_dir") or str(Path(conv.xml_path).parent)
        target = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            directory=start_dir,
            save_filename=conv.default_filename,
            file_types=("JSON files (*.json)",),
        )
        if not target:
            return {"ok": False, "cancelled": True}
        target = target[0] if isinstance(target, (list, tuple)) else target
        if not target.lower().endswith(".json"):
            target += ".json"
        try:
            path = service.save(conv, target)
        except Exception as exc:
            return {"ok": False, "error": service.describe_error(exc)}
        self._settings.set("last_json_dir", str(Path(path).parent))
        return {"ok": True, "path": path}

    def choose_folder(self):
        selected = self._window.create_file_dialog(
            webview.FileDialog.FOLDER, directory=self._settings.get("last_json_dir")
        )
        if not selected:
            return None
        return selected[0] if isinstance(selected, (list, tuple)) else selected

    def save_all(self, item_ids, folder, overwrite=False):
        convs = [self._items[i] for i in item_ids if i in self._items]
        targets = [(c, str(Path(folder) / c.default_filename)) for c in convs]
        existing = [Path(t).name for _, t in targets if os.path.exists(t)]
        if existing and not overwrite:
            return {"ok": False, "conflicts": existing}
        saved, errors = [], []
        for conv, target in targets:
            try:
                saved.append(service.save(conv, target))
            except Exception as exc:
                errors.append(f"{Path(target).name}: {service.describe_error(exc)}")
        self._settings.set("last_json_dir", folder)
        return {"ok": not errors, "saved": saved, "errors": errors, "folder": folder}

    def open_in_explorer(self, path):
        if os.path.isfile(path):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif os.path.isdir(path):
            os.startfile(path)
        return True


def bind_drop(window, api: Api):
    def on_drop(event):
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [f["pywebviewFullPath"] for f in files if f.get("pywebviewFullPath")]
        if not paths:
            return
        results = api._analyze_paths(paths)
        window.evaluate_js(f"window.app && window.app.addResults({json.dumps(results)})")

    def ignore(_event):
        pass

    window.dom.document.events.dragenter += DOMEventHandler(ignore, True, True)
    window.dom.document.events.dragover += DOMEventHandler(ignore, True, True, debounce=500)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)


def main():
    api = Api()
    window = webview.create_window(
        APP_TITLE,
        url=resource_path("ui", "index.html"),
        js_api=api,
        width=1100,
        height=760,
        min_size=(820, 560),
    )
    api.attach(window)
    webview.start(bind_drop, (window, api), debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()
