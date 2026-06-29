# min_conflicts_solver.py
import random
from .base_solver import BaseSolver


class MinConflictsSolver(BaseSolver):
    def __init__(self, problem, step_callback=None, max_steps=10000):
        self.problem = problem
        self.step_callback = step_callback
        self.max_steps = max_steps

    def solve(self):
        current = self._initial_assignment()

        for i in range(1, self.max_steps + 1):
            if self._is_solution(current):
                if self.step_callback:
                    self.step_callback("done", None, None, current.copy())
                return current.copy()

            conflicted = self._get_conflicted_vars(current)
            if not conflicted:
                if self.step_callback:
                    self.step_callback("done", None, None, current.copy())
                return current.copy()

            var = random.choice(conflicted)

            value = self._min_conflicts_value(var, current)

            current[var] = value

            if self.step_callback:
                self.step_callback("assign", var, value, current.copy())

        return None

    def _initial_assignment(self):
        assignment = {}
        for var in self.problem.adjacency:
            assignment[var] = random.choice(self.problem.colors)
        return assignment

    def _is_solution(self, assignment):
        for var, color in assignment.items():
            for neighbor in self.problem.neighbors(var):
                if assignment.get(neighbor) == color:
                    return False
        return True

    def _get_conflicted_vars(self, assignment):
        conflicted = []
        for var, color in assignment.items():
            for neighbor in self.problem.neighbors(var):
                if assignment.get(neighbor) == color:
                    conflicted.append(var)
                    break
        return conflicted

    def _conflicts(self, var, value, assignment):
        count = 0
        for neighbor in self.problem.neighbors(var):
            if assignment.get(neighbor) == value:
                count += 1
        return count

    def _min_conflicts_value(self, var, assignment):
        min_count = float("inf")
        best_values = []
        for value in self.problem.colors:
            count = self._conflicts(var, value, assignment)
            if count < min_count:
                min_count = count
                best_values = [value]
            elif count == min_count:
                best_values.append(value)
        return random.choice(best_values)
