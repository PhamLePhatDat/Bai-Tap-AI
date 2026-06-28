from builtins import len
import time
import threading

from puzzle_logic import (
    bfs, dfs, ids, ucs, a_star, greedy_search,
    simple_hill_climbing, steepest_ascent_hill_climbing,
    stochastic_hill_climbing, random_restart_hill_climbing,
    local_beam_search, simulated_annealing,
    bfs_belief_state,
    and_or_search,
    plan_to_actions,
    actions_to_node,
    get_path, random_state, is_solvable,
    goal, DFS_MAX_DEPTH
)
from puzzle_ui import PuzzleUI


class PuzzleApp:

    def __init__(self):
        self.goal_state    = [row[:] for row in goal]
        self.current_state = random_state(self.goal_state)
        self.path          = []
        self.step_index    = 0
        self.running       = False
        self._after_id     = None
        self._solve_id     = 0

        self.ui = PuzzleUI(
            on_random_cb      = self.on_random,
            on_start_cb       = self.on_start,
            on_stop_cb        = self.on_stop,
            on_set_initial_cb = self.on_set_initial,
            on_set_goal_cb    = self.on_set_goal,
        )

        self.ui.refresh_input_grids(self.current_state, self.goal_state)
        self.ui.draw_grid(self.current_state, self.goal_state)

    def run(self):
        self.ui.mainloop()

    def on_random(self):
        self.running = False
        self._cancel_animation()
        self._solve_id += 1
        self.current_state = random_state(self.goal_state)
        self.path          = []
        self.step_index    = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.refresh_input_grids(self.current_state, self.goal_state)
        self.ui.draw_grid(self.current_state, self.goal_state)

    def on_set_initial(self, state):
        if self.running:
            return
        if not is_solvable(state, self.goal_state):
            self.ui.show_toast("Puzzle này KHÔNG giải được với trạng thái đích hiện tại!")
            return
        self._cancel_animation()
        self.current_state = state
        self.path          = []
        self.step_index    = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.draw_grid(self.current_state, self.goal_state)

    def on_set_goal(self, state):
        if self.running:
            return

        self._cancel_animation()
        self.goal_state = state
        self.path       = []
        self.step_index = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.draw_grid(self.current_state, self.goal_state)

    BELIEF_STATE_1 = [[1, 2, 3], [4, 5, 6], [7, 0, 8]]
    BELIEF_STATE_2 = [[1, 2, 3], [4, 5, 6], [0, 7, 8]]

    def on_start(self):
        algo = self.ui.get_algorithm()

        if algo == "BeliefBFS":
            self.current_state = [row[:] for row in self.BELIEF_STATE_1]
            self.ui.refresh_input_grids(self.BELIEF_STATE_1, self.BELIEF_STATE_2)
            self.ui.draw_grid(self.BELIEF_STATE_1, self.BELIEF_STATE_2)
        else:
            if not is_solvable(self.current_state, self.goal_state):
                self.ui.show_toast("Puzzle này không giải được!")
                return

        self.running = False
        self._cancel_animation()
        self.path       = []
        self.step_index = 0
        self._solve_id += 1
        self.running    = True
        self.ui.set_stat("BƯỚC",        0)
        self.ui.set_stat("TỔNG_BƯỚC",  "...")
        self.ui.set_stat("THỜI_GIAN",  "...")
        self.ui.set_stat("TRẠNG_THÁI", f"Đang giải ({algo})...")
        self.ui.set_buttons(running=True)
        self.ui.clear_steps()

        threading.Thread(target=self._solve_worker, daemon=True).start()

    def on_stop(self):
        if not self.path or self.step_index >= len(self.path):
            return
        if self.running:
            self.running = False
            self._cancel_animation()
            self.ui.set_stat("TRẠNG_THÁI", "Đã tạm dừng")
            self.ui.set_pause_mode(paused=True)
        else:
            self.running = True
            self.ui.set_stat("TRẠNG_THÁI", "Đang chạy...")
            self.ui.set_pause_mode(paused=False)
            self._animate_next()

    def _solve_worker(self):
        my_id = self._solve_id
        algo  = self.ui.get_algorithm()
        t0    = time.time()

        def stop_flag():
            return self._solve_id != my_id

        if algo == "BFS":
            result = bfs(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "DFS":
            result = dfs(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "UCS":
            result = ucs(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "A*":
            result = a_star(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "Greedy":
            result = greedy_search(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "Hill":
            result = simple_hill_climbing(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "Steepest":
            result = steepest_ascent_hill_climbing(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "Stochastic":
            result = stochastic_hill_climbing(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "RandomRestart":
            result = random_restart_hill_climbing(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "LocalBeam":
            result = local_beam_search(self.current_state, self.goal_state, stop_flag=stop_flag, k=3)
        elif algo == "SA":
            result = simulated_annealing(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "BeliefBFS":
            belief_states = [self.BELIEF_STATE_1, self.BELIEF_STATE_2]
            result = bfs_belief_state(belief_states, self.goal_state, stop_flag=stop_flag)
        elif algo == "ANDOR":
            belief_states = [self.current_state]
            plan = and_or_search(belief_states,self.goal_state,max_depth=50,stop_flag=stop_flag)
            if plan is None:
                result = None
            else:
                actions = plan_to_actions(plan)

                result = actions_to_node(
                    self.current_state,
                    actions
                )
        else:
            result = ids(self.current_state, self.goal_state, stop_flag=stop_flag)

        elapsed = time.time() - t0

        if my_id != self._solve_id:
            return

        if result is None:
            hill_algos = ("Hill", "Steepest", "Stochastic", "RandomRestart", "LocalBeam")
            if algo == "SA":
                msg = "SA: Nhiệt độ giảm về Tmin mà chưa tìm được lời giải. Thử lại!"
            elif algo == "BeliefBFS":
                msg = "BeliefBFS: Không tìm được hành động chung cho tất cả belief states!"
            elif algo in hill_algos:
                msg = f"{algo} bị kẹt ở cực trị địa phương (local optimum)!"
            else:
                msg = f"{algo} không tìm được lời giải"
            self.ui.after(0, lambda m=msg: self.ui.show_toast(m))
            self.ui.after(0, lambda: self.ui.set_stat("TRẠNG_THÁI", "Không tìm được"))
            self.ui.after(0, lambda: self.ui.set_buttons(running=False))
            self.running = False
            return

        self.path = get_path(result)
        total     = len(self.path) - 1

        elapsed_str = f"{elapsed*1000:.0f}ms" if elapsed < 1 else f"{elapsed:.2f}s"
        self.ui.after(0, lambda: self.ui.set_stat("TỔNG_BƯỚC",  total))
        self.ui.after(0, lambda: self.ui.set_stat("THỜI_GIAN",  elapsed_str))
        self.ui.after(0, lambda: self.ui.set_stat("TRẠNG_THÁI", "Chờ..."))

        self.ui.after(0, lambda: self.ui.load_steps(self.path))
        self.ui.after(50, self._animate_next)

    def _animate_next(self):
        if not self.running:
            return
        if self.step_index >= len(self.path):
            self.running = False
            self.ui.set_stat("TRẠNG_THÁI", "Hoàn thành")
            self.ui.set_buttons(running=False)
            return

        if self.step_index == 1:
            self.ui.set_stat("TRẠNG_THÁI", "Đang chạy...")

        _, state = self.path[self.step_index]
        if self.step_index >= 1:
            self.ui.set_stat("BƯỚC", self.step_index)

        self.ui.draw_grid(state, self.goal_state)

        self.ui.highlight_step(self.step_index)

        self.step_index += 1
        self._after_id = self.ui.after(self.ui.get_delay_ms(), self._animate_next)

    def _cancel_animation(self):
        if self._after_id is not None:
            self.ui.after_cancel(self._after_id)
            self._after_id = None

    def _reset_stats(self):
        self.ui.set_stat("BƯỚC",        0)
        self.ui.set_stat("TỔNG_BƯỚC",  "—")
        self.ui.set_stat("THỜI_GIAN",  "—")
        self.ui.set_stat("TRẠNG_THÁI", "Chờ...")


if __name__ == "__main__":
    app = PuzzleApp()
    app.run()