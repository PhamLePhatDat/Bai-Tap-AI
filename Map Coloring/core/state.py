# state.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class State:
    assignment: Dict[str, str] = field(default_factory=dict)

    def copy(self) -> "State":
        return State(assignment=self.assignment.copy())
