# base_solver.py

from abc import ABC, abstractmethod

class BaseSolver(ABC):
    @abstractmethod
    def solve(self, problem):
        pass
