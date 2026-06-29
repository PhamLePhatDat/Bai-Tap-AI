# backtracking_solver.py
from .base_solver import BaseSolver


class BacktrackingSolver(BaseSolver):
    def __init__(self, problem, step_callback=None):
        self.problem = problem
        self.step_callback = step_callback

    def solve(self):
        assignment = {}
        return self._backtrack(assignment)

    def _select_unassigned(self, assignment):
        for region in self.problem.adjacency:
            if region not in assignment:
                return region
        return None

    def _backtrack(self, assignment):
        if len(assignment) == len(self.problem.adjacency):
            if self.step_callback:
                self.step_callback("done", None, None, assignment.copy())
            return assignment.copy()

        var = self._select_unassigned(assignment)
        for colour in self.problem.colors:
            assignment[var] = colour
            if self.step_callback:
                self.step_callback("assign", var, colour, assignment.copy())

            if self.problem.is_consistent(assignment):
                result = self._backtrack(assignment)
                if result:
                    return result

            if self.step_callback:
                self.step_callback("backtrack", var, colour, assignment.copy())
            del assignment[var]

        return None
