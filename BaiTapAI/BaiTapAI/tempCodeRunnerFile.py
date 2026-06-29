import importlib.util
import os
import sys
import tkinter as tk

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PUZZLE_DIR = os.path.join(ROOT_DIR, "puzzle solver")
MAP_DIR = os.path.join(ROOT_DIR, "map coloring")
PUZZLE_SCRIPT = os.path.join(PUZZLE_DIR, "app.py")
MAP_SCRIPT = os.path.join(MAP_DIR, "ui", "map_coloring_ui.py")

for extra_path in (PUZZLE_DIR, MAP_DIR):
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)


def load_class_from_path(path, class_name, extra_paths=None):
    if extra_paths is None:
        extra_paths = []
    saved_paths = list(sys.path)
    for p in extra_paths:
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        spec = importlib.util.spec_from_file_location(class_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return getattr(module, class_name)
    finally:
        sys.path[:] = saved_paths

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("8-Puzzle & Map Coloring")
        self.geometry("900x720")
        self.configure(bg="#1E1E2E")

        header = tk.Frame(self, bg="#1E1E2E")
        header.pack(fill="x", pady=12)

        tk.Label(header, text="Chọn ứng dụng:",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1E1E2E", fg="#FFFFFF").pack(side="left", padx=16)

        btn_frame = tk.Frame(header, bg="#1E1E2E")
        btn_frame.pack(side="left", padx=8)

        tk.Button(btn_frame, text="🧩 8-Puzzle Solver", width=18, command=self.show_puzzle).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗺 Map Coloring", width=18, command=self.show_map).pack(side=tk.LEFT, padx=5)

        self.content = tk.Frame(self, bg="#1E1E2E")
        self.content.pack(fill="both", expand=True)

        self.current_app = None
        self.show_puzzle()

    def _replace_content(self, app_frame):
        if self.current_app is not None:
            self.current_app.destroy()
        self.current_app = app_frame
        self.current_app.pack(fill="both", expand=True)

    def show_puzzle(self):
        puzzle_dir = os.path.join(ROOT_DIR, "puzzle solver")
        PuzzleApp = load_class_from_path(PUZZLE_SCRIPT, "PuzzleApp", extra_paths=[puzzle_dir])
        self.title("8-Puzzle Solver")
        app_frame = tk.Frame(self.content, bg="#1E1E2E")
        puzzle_app = PuzzleApp(parent=app_frame)
        puzzle_app.ui.pack(fill="both", expand=True)
        self._replace_content(app_frame)

    def show_map(self):
        map_dir = os.path.join(ROOT_DIR, "map coloring")
        MapColoringApp = load_class_from_path(MAP_SCRIPT, "MapColoringApp", extra_paths=[map_dir])
        self.title("Map Coloring – CSP Solver")
        app_frame = tk.Frame(self.content, bg="#1E1E2E")
        map_app = MapColoringApp(parent=app_frame)
        map_app.pack(fill="both", expand=True)
        self._replace_content(app_frame)

if __name__ == "__main__":
    Launcher().mainloop()