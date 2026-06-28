# constraint.py

class Constraint:
    def __init__(self, var1: str, var2: str):
        self.var1 = var1
        self.var2 = var2

    def is_satisfied(self, assignment: dict) -> bool:
        if self.var1 not in assignment or self.var2 not in assignment:
            return True
        return assignment[self.var1] != assignment[self.var2]
