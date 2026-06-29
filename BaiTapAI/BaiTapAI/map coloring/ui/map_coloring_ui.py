# map_coloring_ui.py
"""
Tkinter UI for the Map Coloring problem.
Features:
- User sets the number of nodes to generate.
- Random planar-ish map generation using Delaunay triangulation via scipy.spatial.
- Solver selection: Backtracking, Forward Checking, AC-3.
- Solve instantly OR animate step-by-step with backtracking visualization.
- Speed control slider for animation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
import time
import threading

try:
    from scipy.spatial import Delaunay  # type: ignore
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

PALETTE = {
    "Red":    "#E74C3C",
    "Green":  "#2ECC71",
    "Blue":   "#3498DB",
    "Yellow": "#F1C40F",
    "Purple": "#9B59B6",
    "Orange": "#E67E22",
    "Teal":   "#1ABC9C",
    "Pink":   "#E91E8C",
}
COLOR_NAMES = list(PALETTE.keys())

NODE_RADIUS = 20
CANVAS_W    = 820
CANVAS_H    = 560
MIN_NODES   = 2
MAX_NODES   = 30

# Animation highlight colours
COLOR_CURRENT    = "#FFD700"   # gold  – node being tried now
COLOR_BACKTRACK  = "#FF4444"   # red   – node being backtracked
COLOR_UNASSIGNED = "#313244"   # dark  – not yet assigned
COLOR_EDGE_DEF   = "#45475A"   # default edge
COLOR_EDGE_CONF  = "#FF4444"   # conflicting edge highlight

def generate_random_map(n_nodes: int):
    margin = 60
    labels = [str(i + 1) for i in range(n_nodes)]

    positions = {}
    min_dist = 100
    attempts = 0
    for label in labels:
        placed = False
        while not placed:
            x = random.randint(margin, CANVAS_W - margin)
            y = random.randint(margin, CANVAS_H - margin)
            if all(math.dist((x, y), positions[l]) >= min_dist
                   for l in positions):
                positions[label] = (x, y)
                placed = True
            attempts += 1
            if attempts > 5000:
                min_dist = max(40, min_dist - 5)
                attempts = 0

    adjacency = {l: set() for l in labels}

    candidate_edges = set()
    if HAS_SCIPY and n_nodes >= 3:
        import numpy as np
        pts = np.array([positions[l] for l in labels])
        tri = Delaunay(pts)
        for simplex in tri.simplices:
            for i in range(3):
                a = labels[simplex[i]]
                b = labels[simplex[(i + 1) % 3]]
                candidate_edges.add(tuple(sorted((a, b))))
    else:
        # Fallback: k nearest neighbours as candidates
        k = min(4, n_nodes - 1)
        for la in labels:
            dists = sorted(
                [(math.dist(positions[la], positions[lb]), lb)
                 for lb in labels if lb != la]
            )
            for _, lb in dists[:k]:
                candidate_edges.add(tuple(sorted((la, lb))))

    node_style = {}
    for label in labels:
        r = random.random()
        if r < 0.20:
            node_style[label] = "isolated"
        elif r < 0.55:
            node_style[label] = "sparse"
        else:
            node_style[label] = "normal"

    for a, b in candidate_edges:
        sa = node_style[a]
        sb = node_style[b]
        if sa == "isolated" or sb == "isolated":
            continue
        if sa == "sparse" or sb == "sparse":
            if random.random() > 0.40:
                continue
        adjacency[a].add(b)
        adjacency[b].add(a)

    return positions, adjacency

class MapColoringApp(tk.Frame):
    def __init__(self, parent=None):
        if parent is None:
            self.root = tk.Tk()
            super().__init__(self.root, bg="#1E1E2E")
            self.root.title("Map Coloring – CSP Solver")
            self.root.resizable(False, False)
            self.pack(fill="both", expand=True)
        else:
            self.root = None
            super().__init__(parent, bg="#1E1E2E")

        self._positions    = {}   # node -> (x, y)
        self._adjacency    = {}   # node -> set of neighbors
        self._solution     = {}   # node -> color name
        self._node_ovals   = {}   # node -> canvas oval id
        self._node_texts   = {}   # node -> canvas text id
        self._edge_ids     = {}   # (a,b) sorted tuple -> canvas line id

        # Animation state
        self._anim_steps   = []   # list of (event, node, color, assignment)
        self._anim_index   = 0
        self._anim_running = False
        self._anim_job     = None  # after() job id
        self._step_counts  = {"assign": 0, "backtrack": 0}

        self._build_left_panel()
        self._build_canvas()

    def _build_left_panel(self):
        panel = tk.Frame(self, bg="#2A2A3E", padx=14, pady=14)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        title = tk.Label(panel, text="Map Coloring\nCSP Solver",
                         font=("Segoe UI", 16, "bold"),
                         bg="#2A2A3E", fg="#CBA6F7")
        title.pack(pady=(0, 20))

        tk.Label(panel, text="Số node:", bg="#2A2A3E", fg="#CDD6F4",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._node_count_var = tk.IntVar(value=8)
        node_frame = tk.Frame(panel, bg="#2A2A3E")
        node_frame.pack(fill=tk.X, pady=(2, 10))
        self._node_spin = tk.Spinbox(
            node_frame,
            from_=MIN_NODES, to=MAX_NODES,
            textvariable=self._node_count_var,
            width=6, font=("Segoe UI", 11),
            bg="#313244", fg="#CDD6F4",
            buttonbackground="#45475A",
            relief=tk.FLAT, highlightthickness=0
        )
        self._node_spin.pack(side=tk.LEFT)
        tk.Label(node_frame, text=f"({MIN_NODES}–{MAX_NODES})",
                 bg="#2A2A3E", fg="#6C7086",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=6)

        self._btn_gen = tk.Button(
            panel, text="🗺  Generate Map",
            command=self._on_generate,
            bg="#89B4FA", fg="#1E1E2E",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=10, pady=6
        )
        self._btn_gen.pack(fill=tk.X, pady=(0, 18))

        ttk.Separator(panel, orient="horizontal").pack(fill=tk.X, pady=4)

        tk.Label(panel, text="Thuật toán:", bg="#2A2A3E", fg="#CDD6F4",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        self._algo_var = tk.StringVar(value="Backtracking")
        algo_options = ["Backtracking", "Forward Checking", "AC-3", "Min-Conflicts"]
        self._algo_menu = ttk.Combobox(
            panel, values=algo_options,
            textvariable=self._algo_var,
            state="readonly", font=("Segoe UI", 10), width=18
        )
        self._algo_menu.pack(pady=(0, 10))

        tk.Label(panel, text="Số màu tối đa:", bg="#2A2A3E", fg="#CDD6F4",
                 font=("Segoe UI", 10)).pack(anchor="w")
        self._color_count_var = tk.IntVar(value=4)
        self._color_spin = tk.Spinbox(
            panel,
            from_=2, to=len(COLOR_NAMES),
            textvariable=self._color_count_var,
            width=6, font=("Segoe UI", 11),
            bg="#313244", fg="#CDD6F4",
            buttonbackground="#45475A",
            relief=tk.FLAT, highlightthickness=0
        )
        self._color_spin.pack(anchor="w", pady=(2, 14))

        ttk.Separator(panel, orient="horizontal").pack(fill=tk.X, pady=4)

        tk.Label(panel, text="Tốc độ animation:", bg="#2A2A3E", fg="#CDD6F4",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        self._speed_var = tk.IntVar(value=5)
        speed_frame = tk.Frame(panel, bg="#2A2A3E")
        speed_frame.pack(fill=tk.X, pady=(0, 4))
        tk.Label(speed_frame, text="Chậm", bg="#2A2A3E", fg="#6C7086",
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self._speed_slider = tk.Scale(
            speed_frame, from_=1, to=10,
            variable=self._speed_var,
            orient=tk.HORIZONTAL, showvalue=False,
            bg="#2A2A3E", fg="#CDD6F4",
            troughcolor="#313244", activebackground="#CBA6F7",
            highlightthickness=0, length=100
        )
        self._speed_slider.pack(side=tk.LEFT)
        tk.Label(speed_frame, text="Nhanh", bg="#2A2A3E", fg="#6C7086",
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)

        btn_frame = tk.Frame(panel, bg="#2A2A3E")
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self._btn_solve = tk.Button(
            btn_frame, text="⚡ Solve",
            command=self._on_solve,
            bg="#A6E3A1", fg="#1E1E2E",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=6, pady=6,
            state=tk.DISABLED
        )
        self._btn_solve.pack(fill=tk.X, pady=(0, 6))

        self._btn_animate = tk.Button(
            btn_frame, text="▶  Animate",
            command=self._on_animate,
            bg="#CBA6F7", fg="#1E1E2E",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=6, pady=6,
            state=tk.DISABLED
        )
        self._btn_animate.pack(fill=tk.X, pady=(0, 6))

        self._btn_pause = tk.Button(
            btn_frame, text="⏸  Pause",
            command=self._on_pause,
            bg="#FAB387", fg="#1E1E2E",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=6, pady=6,
            state=tk.DISABLED
        )
        self._btn_pause.pack(fill=tk.X, pady=(0, 6))

        self._btn_reset = tk.Button(
            btn_frame, text="↺  Reset",
            command=self._on_reset,
            bg="#F38BA8", fg="#1E1E2E",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=6, pady=6,
            state=tk.DISABLED
        )
        self._btn_reset.pack(fill=tk.X, pady=(0, 8))

        ttk.Separator(panel, orient="horizontal").pack(fill=tk.X, pady=4)
        self._status_var = tk.StringVar(value="Nhấn 'Generate Map' để bắt đầu.")
        status_lbl = tk.Label(
            panel, textvariable=self._status_var,
            bg="#2A2A3E", fg="#A6ADC8",
            font=("Segoe UI", 9),
            wraplength=170, justify=tk.LEFT
        )
        status_lbl.pack(pady=(10, 0), anchor="w")

        self._step_label_var = tk.StringVar(value="")
        tk.Label(
            panel, textvariable=self._step_label_var,
            bg="#2A2A3E", fg="#89DCEB",
            font=("Segoe UI", 9), wraplength=170, justify=tk.LEFT
        ).pack(pady=(6, 0), anchor="w")

        self._legend_frame = tk.Frame(panel, bg="#2A2A3E")
        self._legend_frame.pack(pady=(12, 0), fill=tk.X)

    def _build_canvas(self):
        canvas_frame = tk.Frame(self, bg="#181825", bd=0)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            canvas_frame,
            width=CANVAS_W, height=CANVAS_H,
            bg="#181825", highlightthickness=0
        )
        self._canvas.pack(padx=12, pady=12)

        self._canvas.create_text(
            CANVAS_W // 2, CANVAS_H // 2,
            text="Chưa có bản đồ.\nHãy nhấn 'Generate Map'.",
            fill="#45475A", font=("Segoe UI", 14),
            tags="placeholder"
        )

    def _on_generate(self):
        n = self._node_count_var.get()
        if not (MIN_NODES <= n <= MAX_NODES):
            messagebox.showerror("Lỗi",
                f"Số node phải từ {MIN_NODES} đến {MAX_NODES}.")
            return

        self._stop_animation()
        self._solution = {}
        self._anim_steps = []
        self._step_counts = {"assign": 0, "backtrack": 0}
        self._step_label_var.set("")
        self._status_var.set(f"Đã tạo bản đồ {n} node.")
        self._positions, self._adjacency = generate_random_map(n)
        self._btn_solve.config(state=tk.NORMAL)
        self._btn_animate.config(state=tk.NORMAL)
        self._btn_reset.config(state=tk.NORMAL)
        self._btn_pause.config(state=tk.DISABLED)
        self._draw_map()
        self._clear_legend()

    def _on_solve(self):
        if not self._adjacency:
            return
        self._stop_animation()

        n_colors = self._color_count_var.get()
        colors   = COLOR_NAMES[:n_colors]
        algo     = self._algo_var.get()

        from core.map_coloring_problem import MapColoringProblem
        problem = MapColoringProblem(
            {k: set(v) for k, v in self._adjacency.items()},
            colors
        )

        t0 = time.perf_counter()
        if algo == "Backtracking":
            from algorithms.backtracking_solver import BacktrackingSolver
            solver = BacktrackingSolver(problem)
        elif algo == "Forward Checking":
            from algorithms.forward_checking_solver import ForwardCheckingSolver
            solver = ForwardCheckingSolver(problem)
        elif algo == "AC-3":
            from algorithms.ac3_solver import AC3Solver
            solver = AC3Solver(problem)
        else:  # Min-Conflicts
            from algorithms.min_conflicts_solver import MinConflictsSolver
            solver = MinConflictsSolver(problem)

        solution = solver.solve()
        elapsed  = time.perf_counter() - t0

        if solution:
            self._solution = solution
            self._draw_map()          # reset highlights
            self._apply_colors()
            n_used = len(set(solution.values()))
            self._status_var.set(
                f"Giải xong!\nThuật toán: {algo}\n"
                f"Màu dùng: {n_used}/{n_colors}\n"
                f"Thời gian: {elapsed*1000:.2f} ms"
            )
            self._draw_legend(set(solution.values()))
        else:
            self._status_var.set(
                f"Không có lời giải\nvới {n_colors} màu.")
            messagebox.showwarning("Không tìm được lời giải",
                f"Bản đồ này không thể tô với {n_colors} màu.\n"
                "Hãy thử tăng số màu hoặc generate bản đồ mới.")

    def _on_animate(self):
        if not self._adjacency:
            return
        self._stop_animation()
        self._draw_map()       # reset to clean state
        self._clear_legend()
        self._solution = {}
        self._step_counts = {"assign": 0, "backtrack": 0}
        self._step_label_var.set("")

        n_colors = self._color_count_var.get()
        colors   = COLOR_NAMES[:n_colors]
        algo     = self._algo_var.get()

        from core.map_coloring_problem import MapColoringProblem
        problem = MapColoringProblem(
            {k: set(v) for k, v in self._adjacency.items()},
            colors
        )

        steps = []

        def record(event, node, color, assignment):
            steps.append((event, node, color, assignment))

        if algo == "Backtracking":
            from algorithms.backtracking_solver import BacktrackingSolver
            solver = BacktrackingSolver(problem, step_callback=record)
        elif algo == "Forward Checking":
            from algorithms.forward_checking_solver import ForwardCheckingSolver
            solver = ForwardCheckingSolver(problem, step_callback=record)
        elif algo == "AC-3":
            from algorithms.ac3_solver import AC3Solver
            solver = AC3Solver(problem, step_callback=record)
        else:  # Min-Conflicts
            from algorithms.min_conflicts_solver import MinConflictsSolver
            solver = MinConflictsSolver(problem, step_callback=record)

        solution = solver.solve()
        self._anim_steps = steps
        self._anim_index = 0
        self._anim_running = True

        self._btn_animate.config(state=tk.DISABLED)
        self._btn_solve.config(state=tk.DISABLED)
        self._btn_pause.config(state=tk.NORMAL)

        if not solution and not steps:
            self._status_var.set(f"❌ Không có lời giải\nvới {n_colors} màu.")
            messagebox.showwarning("Không tìm được lời giải",
                f"Bản đồ này không thể tô với {n_colors} màu.\n"
                "Hãy thử tăng số màu hoặc generate bản đồ mới.")
            self._anim_running = False
            self._btn_animate.config(state=tk.NORMAL)
            self._btn_solve.config(state=tk.NORMAL)
            self._btn_pause.config(state=tk.DISABLED)
            return

        total = len(steps)
        self._status_var.set(
            f"▶ Đang animation...\nThuật toán: {algo}\nTổng bước: {total}"
        )
        self._play_next_step()

    def _on_pause(self):
        if self._anim_running:
            self._anim_running = False
            if self._anim_job:
                self.after_cancel(self._anim_job)
                self._anim_job = None
            self._btn_pause.config(text="▶  Resume")
        else:
            # Resume
            self._anim_running = True
            self._btn_pause.config(text="⏸  Pause")
            self._play_next_step()

    def _on_reset(self):
        self._stop_animation()
        self._solution = {}
        self._anim_steps = []
        self._step_counts = {"assign": 0, "backtrack": 0}
        self._step_label_var.set("")
        self._status_var.set("Đã reset. Nhấn Solve hoặc Animate để giải lại.")
        self._draw_map()
        self._clear_legend()
        self._btn_pause.config(text="⏸  Pause", state=tk.DISABLED)
        self._btn_animate.config(state=tk.NORMAL)
        self._btn_solve.config(state=tk.NORMAL)

    def _stop_animation(self):
        self._anim_running = False
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def _play_next_step(self):
        if not self._anim_running:
            return
        if self._anim_index >= len(self._anim_steps):
            # Animation finished
            self._anim_running = False
            self._btn_animate.config(state=tk.NORMAL)
            self._btn_solve.config(state=tk.NORMAL)
            self._btn_pause.config(state=tk.DISABLED, text="⏸  Pause")
            return

        event, node, color, assignment = self._anim_steps[self._anim_index]
        self._anim_index += 1

        self._apply_animation_step(event, node, color, assignment)

        # Speed: slider 1-10 → delay 600ms down to 20ms
        speed  = self._speed_var.get()   # 1..10
        delay  = int(620 - speed * 60)   # 560..20 ms
        self._anim_job = self.after(delay, self._play_next_step)

    def _apply_animation_step(self, event, node, color, assignment):
        """Update the canvas for one animation step."""
        if event == "assign":
            self._step_counts["assign"] += 1
            # Paint node with its attempted colour
            hex_c = PALETTE.get(color, COLOR_CURRENT)
            self._set_node_color(node, hex_c, outline=COLOR_CURRENT, outline_width=3)
            # Highlight conflicting edges red
            self._update_edge_highlights(assignment)
            self._update_step_label()
            algo = self._algo_var.get()
            self._status_var.set(
                f"▶ Thử: node {node} → {color}\n"
                f"Bước #{self._step_counts['assign']}\n"
                f"Backtrack: {self._step_counts['backtrack']}"
            )

        elif event == "backtrack":
            self._step_counts["backtrack"] += 1
            # Flash red then clear
            self._set_node_color(node, COLOR_BACKTRACK, outline="#FF8888", outline_width=3)
            # Clear the node back to unassigned after a short flash
            self.after(120, lambda n=node: self._set_node_color(
                n, COLOR_UNASSIGNED, outline="#CDD6F4", outline_width=2))
            self._update_edge_highlights(assignment)
            self._update_step_label()
            self._status_var.set(
                f"↩ Backtrack: node {node}\n"
                f"Bước #{self._step_counts['assign']}\n"
                f"Backtrack: {self._step_counts['backtrack']}"
            )

        elif event == "done":
            # Final solution – apply all colours properly
            self._solution = assignment
            self._draw_map()
            self._apply_colors()
            # Reset all edge colours
            self._reset_edges()
            n_used = len(set(assignment.values()))
            algo   = self._algo_var.get()
            n_col  = self._color_count_var.get()
            self._status_var.set(
                f"Giải xong!\nThuật toán: {algo}\n"
                f"Màu dùng: {n_used}/{n_col}\n"
                f"Assign: {self._step_counts['assign']}\n"
                f"Backtrack: {self._step_counts['backtrack']}"
            )
            self._draw_legend(set(assignment.values()))
            self._update_step_label()

    def _update_step_label(self):
        a = self._step_counts["assign"]
        b = self._step_counts["backtrack"]
        self._step_label_var.set(f"Assign: {a}  |  Backtrack: {b}")

    def _draw_map(self):
        self._canvas.delete("all")
        self._node_ovals.clear()
        self._node_texts.clear()
        self._edge_ids.clear()

        # Draw edges first
        drawn_edges = set()
        for node, neighbors in self._adjacency.items():
            x1, y1 = self._positions[node]
            for nb in neighbors:
                edge = tuple(sorted((node, nb)))
                if edge in drawn_edges:
                    continue
                drawn_edges.add(edge)
                x2, y2 = self._positions[nb]
                lid = self._canvas.create_line(
                    x1, y1, x2, y2,
                    fill=COLOR_EDGE_DEF, width=2, tags="edge"
                )
                self._edge_ids[edge] = lid

        # Draw nodes
        for node, (x, y) in self._positions.items():
            color = PALETTE.get(self._solution.get(node, ""), COLOR_UNASSIGNED)
            r = NODE_RADIUS
            oid = self._canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=color, outline="#CDD6F4", width=2,
                tags=("node", f"node_{node}")
            )
            tid = self._canvas.create_text(
                x, y, text=node,
                fill="#CDD6F4", font=("Segoe UI", 9, "bold"),
                tags=("label", f"label_{node}")
            )
            self._node_ovals[node] = oid
            self._node_texts[node] = tid

    def _apply_colors(self):
        """Paint each node according to self._solution."""
        for node, color_name in self._solution.items():
            oid = self._node_ovals.get(node)
            if oid:
                hex_color = PALETTE.get(color_name, COLOR_UNASSIGNED)
                self._canvas.itemconfig(oid, fill=hex_color)

    def _set_node_color(self, node, fill, outline="#CDD6F4", outline_width=2):
        oid = self._node_ovals.get(node)
        if oid:
            self._canvas.itemconfig(oid, fill=fill, outline=outline,
                                    width=outline_width)

    def _update_edge_highlights(self, assignment):
        """Colour conflicting edges red, others default."""
        # Reset all edges first
        for lid in self._edge_ids.values():
            self._canvas.itemconfig(lid, fill=COLOR_EDGE_DEF, width=2)
        # Highlight conflicts
        for (a, b), lid in self._edge_ids.items():
            ca = assignment.get(a)
            cb = assignment.get(b)
            if ca and cb and ca == cb:
                self._canvas.itemconfig(lid, fill=COLOR_EDGE_CONF, width=3)

    def _reset_edges(self):
        for lid in self._edge_ids.values():
            self._canvas.itemconfig(lid, fill=COLOR_EDGE_DEF, width=2)

    def _draw_legend(self, used_colors):
        self._clear_legend()
        tk.Label(self._legend_frame, text="Chú thích màu:",
                 bg="#2A2A3E", fg="#CDD6F4",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        for cname in used_colors:
            row = tk.Frame(self._legend_frame, bg="#2A2A3E")
            row.pack(anchor="w", pady=2)
            swatch = tk.Canvas(row, width=16, height=16,
                               bg=PALETTE.get(cname, "#888"),
                               highlightthickness=1,
                               highlightbackground="#45475A")
            swatch.pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=cname, bg="#2A2A3E", fg="#CDD6F4",
                     font=("Segoe UI", 9)).pack(side=tk.LEFT)

    def _clear_legend(self):
        for widget in self._legend_frame.winfo_children():
            widget.destroy()

def launch_ui():
    app = MapColoringApp()
    app.root.mainloop()


def display_solution(solution):
    """Simple console print (kept for backward compatibility)."""
    print("Solution:")
    for region, colour in solution.items():
        print(f"  {region} -> {colour}")


def display_map(adjacency):
    for region, neighbors in adjacency.items():
        print(f"{region}: {', '.join(sorted(neighbors))}")


if __name__ == "__main__":
    launch_ui()
