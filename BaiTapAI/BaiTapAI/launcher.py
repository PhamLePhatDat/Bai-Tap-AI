import importlib.util
import os
import sys
import tkinter as tk

ROOT_DIR      = os.path.dirname(os.path.abspath(__file__))
PUZZLE_DIR    = os.path.join(ROOT_DIR, "puzzle solver")
MAP_DIR       = os.path.join(ROOT_DIR, "map coloring")
TTT_DIR       = os.path.join(ROOT_DIR, "tic tac toe")
PUZZLE_SCRIPT = os.path.join(PUZZLE_DIR, "app.py")
MAP_SCRIPT    = os.path.join(MAP_DIR, "ui", "map_coloring_ui.py")
TTT_SCRIPT    = os.path.join(TTT_DIR, "tictactoe_ui.py")

for extra_path in (PUZZLE_DIR, MAP_DIR, TTT_DIR):
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
        spec   = importlib.util.spec_from_file_location(class_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return getattr(module, class_name)
    finally:
        sys.path[:] = saved_paths


BG       = "#1E1E2E"
BTN_NORM = {"bg": "#313244", "fg": "#CDD6F4", "relief": "flat",
            "font": ("Segoe UI", 11, "bold"), "padx": 18, "pady": 8,
            "cursor": "hand2", "activebackground": "#45475A",
            "activeforeground": "#CDD6F4", "bd": 0}
BTN_ACT  = {**BTN_NORM, "bg": "#CBA6F7", "fg": "#1E1E2E",
            "activebackground": "#B4A0F0"}


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Game Suite")
        self.geometry("980x740")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._active_key = None
        self._btn_refs   = {}

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(14, 0), padx=16)

        tk.Label(header, text="AI Game Suite",
                 font=("Segoe UI", 18, "bold"),
                 bg=BG, fg="#CBA6F7").pack(side="left")

        btn_frame = tk.Frame(header, bg=BG)
        btn_frame.pack(side="right")

        apps = [
            ("puzzle",  "8-Puzzle Solver",  self.show_puzzle),
            ("map",     "Map Coloring",      self.show_map),
            ("ttt",     "XO",           self.show_ttt),
        ]
        for key, label, cmd in apps:
            btn = tk.Button(btn_frame, text=label, command=cmd, **BTN_NORM)
            btn.pack(side="left", padx=4)
            self._btn_refs[key] = btn

        # Gạch dưới header
        tk.Frame(self, bg="#45475A", height=1).pack(fill="x", padx=0, pady=(10, 0))

        # Nội dung chính
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)

        self.current_app = None
        self.show_puzzle()

    def _set_active_btn(self, key):
        for k, btn in self._btn_refs.items():
            cfg = BTN_ACT if k == key else BTN_NORM
            btn.config(**cfg)
        self._active_key = key

    def _replace_content(self, frame):
        if self.current_app is not None:
            self.current_app.destroy()
        self.current_app = frame
        self.current_app.pack(fill="both", expand=True)

    # Hiển thị từng app

    def show_puzzle(self):
        self._set_active_btn("puzzle")
        self.title("8-Puzzle Solver")
        PuzzleApp = load_class_from_path(PUZZLE_SCRIPT, "PuzzleApp",
                                         extra_paths=[PUZZLE_DIR])
        wrapper = tk.Frame(self.content, bg=BG)
        app     = PuzzleApp(parent=wrapper)
        app.ui.pack(fill="both", expand=True)
        self._replace_content(wrapper)

    def show_map(self):
        self._set_active_btn("map")
        self.title("Map Coloring – CSP Solver")
        MapColoringApp = load_class_from_path(MAP_SCRIPT, "MapColoringApp",
                                              extra_paths=[MAP_DIR])
        wrapper = tk.Frame(self.content, bg=BG)
        map_app = MapColoringApp(parent=wrapper)
        map_app.pack(fill="both", expand=True)
        self._replace_content(wrapper)

    def show_ttt(self):
        self._set_active_btn("ttt")
        self.title("XO 3×3 – Người vs Máy")
        TicTacToeApp = load_class_from_path(TTT_SCRIPT, "TicTacToeApp",
                                            extra_paths=[TTT_DIR])
        wrapper = tk.Frame(self.content, bg=BG)
        ttt_app = TicTacToeApp(parent=wrapper)
        ttt_app.pack(fill="both", expand=True)
        self._replace_content(wrapper)


if __name__ == "__main__":
    Launcher().mainloop()
