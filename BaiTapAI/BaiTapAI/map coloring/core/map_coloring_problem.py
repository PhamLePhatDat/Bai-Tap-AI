from typing import Dict, List, Set, Tuple

class MapColoringProblem:
    def __init__(self, adjacency: Dict[str, Set[str]], colors: List[str]):
        self.adjacency = adjacency
        self.colors = colors

    def neighbors(self, region: str) -> Set[str]:
        return self.adjacency.get(region, set())

    def is_consistent(self, assignment: Dict[str, str]) -> bool:
        for region, color in assignment.items():
            for neighbor in self.neighbors(region):
                if assignment.get(neighbor) == color:
                    return False
        return True

    def unassigned_regions(self, assignment: Dict[str, str]) -> List[str]:
        return [r for r in self.adjacency if r not in assignment]

    def __repr__(self) -> str:
        return f"MapColoringProblem(regions={list(self.adjacency.keys())}, colors={self.colors})"
