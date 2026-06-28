# forward_checking_solver.py
from .base_solver import BaseSolver


class ForwardCheckingSolver(BaseSolver):
    def __init__(self, problem, step_callback=None):
        self.problem = problem
        self.domains = {var: set(problem.colors) for var in problem.adjacency}
        self.step_callback = step_callback

    def solve(self):
        assignment = {}
        return self._backtrack(assignment, self.domains.copy())

    def _select_unassigned(self, assignment, domains):
        unassigned = [v for v in self.problem.adjacency if v not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda var: len(domains[var]))

    def _forward_check(self, var, value, domains, assignment):
        new_domains = {v: domains[v].copy() for v in domains}
        new_domains[var] = {value}
        for neighbor in self.problem.neighbors(var):
            if neighbor in assignment:
                continue
            if value in new_domains[neighbor]:
                new_domains[neighbor].remove(value)
                if not new_domains[neighbor]:
                    return None
        return new_domains

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
                new_domains = self._forward_check(var, value, domains, assignment)
                if new_domains is not None:
                    result = self._backtrack(assignment, new_domains)
                    if result:
                        return result

            if self.step_callback:
                self.step_callback("backtrack", var, value, assignment.copy())
            del assignment[var]

        return None
