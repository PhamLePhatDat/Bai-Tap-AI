# ac3_solver.py
from collections import deque
from .base_solver import BaseSolver


class AC3Solver(BaseSolver):
    def __init__(self, problem, step_callback=None):
        self.problem = problem
        self.domains = {var: set(problem.colors) for var in problem.adjacency}
        self.step_callback = step_callback

    def solve(self):
        if not self._ac3():
            return None
        assignment = {}
        return self._backtrack(assignment, {v: d.copy() for v, d in self.domains.items()})

    def _ac3(self):
        queue = deque()
        for xi in self.problem.adjacency:
            for xj in self.problem.neighbors(xi):
                queue.append((xi, xj))

        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                if not self.domains[xi]:
                    return False
                for xk in self.problem.neighbors(xi):
                    queue.append((xk, xi))
        return True

    def _revise(self, xi, xj):
        removed = False
        for x in list(self.domains[xi]):
            if not any(y != x for y in self.domains[xj]):
                self.domains[xi].discard(x)
                removed = True
        return removed

    def _select_unassigned(self, assignment, domains):
        unassigned = [v for v in self.problem.adjacency if v not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda var: len(domains[var]))

    def _backtrack(self, assignment, domains):
        if len(assignment) == len(self.problem.adjacency):
            if self.step_callback:
                self.step_callback("done", None, None, assignment.copy())
            return assignment.copy()

        var = self._select_unassigned(assignment, domains)
        for value in list(domains[var]):
            assignment[var] = value
            if self.step_callback:
                self.step_callback("assign", var, value, assignment.copy())

            if self.problem.is_consistent(assignment):
                new_domains = {v: domains[v].copy() for v in domains}
                new_domains[var] = {value}
                result = self._backtrack(assignment, new_domains)
                if result:
                    return result

            if self.step_callback:
                self.step_callback("backtrack", var, value, assignment.copy())
            del assignment[var]

        return None
