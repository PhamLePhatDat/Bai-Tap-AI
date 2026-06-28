from builtins import abs, all, dict, frozenset, isinstance, iter, len, list, min, next, range, set, sum, tuple
import heapq
import math
import re
import random
from collections import deque

actions   = ["U", "D", "L", "R"]
goal      = [[1, 2, 3], [4, 0, 5], [6, 7, 8]]

DFS_MAX_DEPTH = 2000


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j


def to_tuple(state):
    return tuple(tuple(row) for row in state)


def move(state, action):
    r, c = find_zero(state)
    ns = [row[:] for row in state]
    if   action == "U" and r > 0: ns[r][c], ns[r-1][c] = ns[r-1][c], ns[r][c]
    elif action == "D" and r < 2: ns[r][c], ns[r+1][c] = ns[r+1][c], ns[r][c]
    elif action == "L" and c > 0: ns[r][c], ns[r][c-1] = ns[r][c-1], ns[r][c]
    elif action == "R" and c < 2: ns[r][c], ns[r][c+1] = ns[r][c+1], ns[r][c]
    return ns


def count_misplaced(state, goal_state):
    if goal_state is None:
        goal_state = goal
    count = 0
    for i in range(3):
        for j in range(3):
            if state[i][j] != 0 and state[i][j] != goal_state[i][j]:
                count += 1
    return count

def _count_inversions(state):
    flat = [x for row in state for x in row if x != 0]
    return sum(flat[i] > flat[j]
               for i in range(len(flat))
               for j in range(i + 1, len(flat)))


def is_solvable(initial_state, goal_state=None):
    if goal_state is None:
        goal_state = goal
    return _count_inversions(initial_state) % 2 == _count_inversions(goal_state) % 2


def parse_state(text):
    text = text.strip()
    if len(text.replace(" ", "")) == 9 and " " not in text:
        nums = [int(c) for c in text]
    else:
        nums = list(map(int, re.findall(r'\d+', text)))
    
    if len(nums) != 9:
        raise ValueError(f"Cần đúng 9 số, nhận được {len(nums)}")
    if sorted(nums) != list(range(9)):
        raise ValueError("Cần đủ các số từ 0 đến 8, không trùng lặp")
    return [nums[i*3:(i+1)*3] for i in range(3)]


def random_state(goal_state=None):
    if goal_state is None:
        goal_state = goal
    nums = list(range(9))
    while True:
        random.shuffle(nums)
        state = [nums[i*3:(i+1)*3] for i in range(3)]
        if is_solvable(state, goal_state) and state != goal_state:
            return state

class Node:
    def __init__(self, state, parent=None, cost=0, action="" ,step = 0,g_cost=0, h_cost=0, belief=None):
        self.state  = state
        self.parent = parent
        self.cost   = cost
        self.action = action
        self.step = step
        self.g_cost = g_cost
        self.h_cost = h_cost
        self._belief = belief

    def __lt__(self, other):
        return self.cost < other.cost


def bfs(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    root = Node(initial_state)
    if root.state == goal_state:
        return root

    frontier        = deque([root])
    explored        = set()
    frontier_states = {to_tuple(initial_state)}

    while frontier:
        if stop_flag and stop_flag():
            return None

        node = frontier.popleft()
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)
        explored.add(node_tuple)

        for action in actions:
            child_state = move(node.state, action)
            child_tuple = to_tuple(child_state)
            if child_tuple not in explored and child_tuple not in frontier_states:
                child = Node(child_state, node, node.cost + 1, action)
                if child_state == goal_state:
                    return child
                frontier.append(child)
                frontier_states.add(child_tuple)

    return None

def dfs(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    root = Node(initial_state)

    if root.state == goal_state:
        return root

    frontier = [root]
    frontier_states = {to_tuple(initial_state)}
    explored = set()

    while frontier:
        if stop_flag and stop_flag():        
            return None

        node = frontier.pop()
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)
        explored.add(node_tuple)

        if node.cost >= DFS_MAX_DEPTH:
            continue

        for action in actions:
            child_state = move(node.state, action)

            if child_state == node.state:
                continue

            child = to_tuple(child_state)
            if child not in explored and child not in frontier_states:
                child_node = Node(child_state, node, node.cost + 1, action)
                if child_state == goal_state:
                    return child_node
                frontier.append(child_node)
                frontier_states.add(child)
    return None

def ids(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    t = 0
    while True:
        if stop_flag and stop_flag():
            return None
        result = _depth_limited_search(initial_state, goal_state, limit=t,
                                       stop_flag=stop_flag)
        if result != "cutoff":
            return result
        t += 1

def _depth_limited_search(initial_state, goal_state, limit, stop_flag=None):
    found_cutoff = False
    root = Node(initial_state)

    if root.state == goal_state:
        return root

    initial_tuple = to_tuple(initial_state)
    stack = [(root, {initial_tuple})]

    while stack:
        if stop_flag and stop_flag():
            return None

        node, path_set = stack.pop()

        if node.state == goal_state:
            return node

        if node.cost >= limit:
            found_cutoff = True
            continue

        for action in actions:
            child_state = move(node.state, action)
            child_tuple = to_tuple(child_state)

            if child_tuple in path_set:
                continue

            child_node = Node(child_state, node, node.cost + 1, action)

            if child_state == goal_state:
                return child_node

            child_path_set = path_set | {child_tuple}
            stack.append((child_node, child_path_set))

    return "cutoff" if found_cutoff else None

def ucs_cost(state, goal_state, step=0):
    if goal_state is None:
        goal_state = goal
    if state == goal_state:
        return step
    
    cost = 0
    for i in range(3):
        for j in range(3):
            if state[i][j] == goal_state[i][j]:
                continue
            cost += 1
    return cost + step

def ucs(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    if initial_state == goal_state:
        return Node(initial_state)

    root = Node(initial_state, cost=0, step=0)
    frontier = []
    heapq.heappush(frontier, (root.cost, root))
    explored = set()
    frontier_states = {to_tuple(initial_state)}

    while frontier:
        if stop_flag and stop_flag():
            return None

        _, node = heapq.heappop(frontier)
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)

        if node_tuple in explored:
            continue
        explored.add(node_tuple)

        if node.state == goal_state:
            return node

        for action in actions:
            child_state = move(node.state, action)
            if child_state == node.state:
                continue
            child_tuple = to_tuple(child_state)
            if child_tuple not in explored and child_tuple not in frontier_states:
                child = Node(child_state, node, node.cost + 1, action, node.step + 1)
                heapq.heappush(frontier, (child.cost, child))
                frontier_states.add(child_tuple)

    return None

def greedy_search(initial_state, goal_state, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    root = Node(initial_state)
    root.cost = h_cost(initial_state, goal_state)
    
    frontier = []
    heapq.heappush(frontier, (root.cost, root))

    reached = set()
    frontier_states = {to_tuple(initial_state)}

    while frontier:
        if stop_flag and stop_flag():
            return None

        _, node = heapq.heappop(frontier)
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)

        if node.state == goal_state:
            return node
        
        reached.add(node_tuple)

        for action in actions:
            child_state = move(node.state, action)
            if child_state == node.state:
                continue 

            children_tuple = to_tuple(child_state)
            if children_tuple not in reached and children_tuple not in frontier_states:
                child_node = Node(child_state, parent=node, action=action)
                child_node.cost = h_cost(child_state, goal_state)
                heapq.heappush(frontier, (child_node.cost, child_node))
                frontier_states.add(children_tuple)
            else:
                continue
    return None

def a_star(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    if initial_state == goal_state:
        return Node(initial_state)

    root = Node(initial_state,
                cost=h_cost(initial_state, goal_state),
                g_cost=0,
                h_cost=h_cost(initial_state, goal_state))

    frontier = [(root.cost, root)]
    frontier_states = {to_tuple(initial_state): root}
    reached = {}  # tuple -> g_cost tốt nhất đã biết

    while frontier:
        if stop_flag and stop_flag():
            return None

        frontier.sort(key=lambda x: x[0])
        _, node = frontier.pop(0)
        node_tuple = to_tuple(node.state)

        if node_tuple in reached and node.g_cost >= reached[node_tuple]:
            continue

        if node.state == goal_state:
            return node

        frontier_states.pop(node_tuple, None)
        reached[node_tuple] = node.g_cost

        for action in actions:
            child_state = move(node.state, action)
            if child_state == node.state:
                continue

            child_tuple  = to_tuple(child_state)
            child_g_cost = node.g_cost + 1
            child_h_cost = h_cost(child_state, goal_state)
            child_f_cost = child_g_cost + child_h_cost

            child_node = Node(child_state, node,
                              cost=child_f_cost,
                              action=action,
                              step=node.step + 1,
                              g_cost=child_g_cost,
                              h_cost=child_h_cost)

            if child_tuple in reached and child_g_cost >= reached[child_tuple]:
                continue
            if child_tuple in frontier_states:
                if child_g_cost < frontier_states[child_tuple].g_cost:
                    frontier_states[child_tuple] = child_node
                    frontier.append((child_f_cost, child_node))
            else:
                frontier_states[child_tuple] = child_node
                frontier.append((child_f_cost, child_node))

    return None

def simple_hill_climbing(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal
    root = Node(initial_state, cost=h_cost(initial_state, goal_state))

    if root.state == goal_state:
        return root

    current_node = root

    while True:
        if stop_flag and stop_flag():
            return None

        found_better_node = False
        for action in actions:
            child_state = move(current_node.state, action)
            if child_state == current_node.state:
                continue
            child_node = Node(child_state, cost=h_cost(child_state, goal_state),
                              parent=current_node, action=action)
            if child_node.cost <= current_node.cost:
                current_node = child_node
                found_better_node = True
                if current_node.state == goal_state:
                    return current_node
                break

        if not found_better_node:
            return None

def steepest_ascent_hill_climbing(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal
    root = Node(initial_state, cost=h_cost(initial_state, goal_state))

    if root.state == goal_state:
        return root

    current_node = root

    while True:
        if stop_flag and stop_flag():
            return None

        neighbors = []
        for action in actions:
            child_state = move(current_node.state, action)
            if child_state == current_node.state:
                continue
            child_node = Node(child_state, cost=h_cost(child_state, goal_state),
                              parent=current_node, action=action)
            neighbors.append(child_node)

        if not neighbors:
            return None

        best_neighbor = min(neighbors, key=lambda n: n.cost)
        if best_neighbor.cost <= current_node.cost:
            current_node = best_neighbor
            if current_node.state == goal_state:
                return current_node
        else:
            return None

def stochastic_hill_climbing(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal
    root = Node(initial_state, cost=h_cost(initial_state, goal_state))

    if root.state == goal_state:
        return root

    current_node = root

    while True:
        if stop_flag and stop_flag():
            return None

        neighbors = []
        for action in actions:
            child_state = move(current_node.state, action)
            if child_state == current_node.state:
                continue
            child_node = Node(child_state, cost=h_cost(child_state, goal_state),
                              parent=current_node, action=action)
            if child_node.cost <= current_node.cost:
                neighbors.append(child_node)

        if not neighbors:
            return None

        current_node = random.choice(neighbors)
        if current_node.state == goal_state:
            return current_node
        
    return None

def random_restart_hill_climbing(initial_state, goal_state=None, stop_flag=None):
    max_restarts = 100

    for i in range(max_restarts):
        if stop_flag and stop_flag():
            return None

        if goal_state is None:
            goal_state = goal
        current_state = initial_state
        current_node = Node(current_state, cost=h_cost(current_state, goal_state))

        if current_node.state == goal_state:
            return current_node

        while True:
            if stop_flag and stop_flag():
                return None

            best_neighbors = []
            for action in actions:
                child_state = move(current_node.state, action)
                if child_state == current_node.state:
                    continue
                child_node = Node(child_state, cost=h_cost(child_state, goal_state),
                                  parent=current_node, action=action)
                if child_node.cost <= current_node.cost:
                    best_neighbors.append(child_node)

            if not best_neighbors:
                break
            else:
                current_node = random.choice(best_neighbors)
                if current_node.state == goal_state:
                    return current_node
                
    return None

def local_beam_search(initial_state, goal_state=None, stop_flag=None, k=3):
    if goal_state is None:
        goal_state = goal

    initial_neighbors = []
    for action in actions:
        child_state = move(initial_state, action)
        if child_state == initial_state:
            continue
        initial_neighbors.append(
            Node(child_state, parent=Node(initial_state), action=action,
                 cost=h_cost(child_state, goal_state))
        )

    initial_neighbors.sort(key=lambda n: n.cost)

    if len(initial_neighbors) >= k:
        current_nodes = initial_neighbors[:k]
    else:
        current_nodes = initial_neighbors 

    for i in range(99999): # Tránh vòng lặp vô hạn không lường trước
        if stop_flag and stop_flag():
            return None

        seen = {}
        for node in current_nodes:
            for action in actions:
                child_state = move(node.state, action)
                if child_state == node.state:
                    continue
                child_tuple = to_tuple(child_state)
                child_node = Node(
                    child_state,
                    parent=node,
                    action=action,
                    cost=h_cost(child_state, goal_state)
                )

                if child_tuple not in seen or child_node.cost < seen[child_tuple].cost:
                    seen[child_tuple] = child_node

        neighbor_states = list(seen.values())
        if not neighbor_states:
            return None

        for neighbor in neighbor_states:
            if neighbor.state == goal_state:
                return neighbor

        neighbor_states.sort(key=lambda n: n.cost)

        if len(neighbor_states) >= k:
            new_nodes = neighbor_states[:k]
        else:
            new_nodes = neighbor_states  

        old_tuples = {to_tuple(n.state) for n in current_nodes}
        new_tuples = {to_tuple(n.state) for n in new_nodes}
        if new_tuples == old_tuples or new_tuples.issubset(old_tuples):
            return None

        current_nodes = new_nodes
    return None

def simulated_annealing(initial_state, goal_state=None, stop_flag=None,
                        T0=100.0, Tmin=0.001, alpha=0.995):
    if goal_state is None:
        goal_state = goal

    if initial_state == goal_state:
        return Node(initial_state)

    max_restarts = 30         

    for _ in range(max_restarts):
        if stop_flag and stop_flag():
            return None

        current_node = Node(initial_state, cost=h_cost(initial_state, goal_state))
        T = T0

        while T > Tmin:
            if stop_flag and stop_flag():
                return None

            if current_node.state == goal_state:
                return current_node

            neighbors = []
            for action in actions:
                child_state = move(current_node.state, action)
                if child_state == current_node.state:
                    continue
                child_node = Node(child_state,
                                  cost=h_cost(child_state, goal_state),
                                  parent=current_node,
                                  action=action)
                neighbors.append(child_node)

            if not neighbors:
                break

            next_node = random.choice(neighbors)
            delta = next_node.cost - current_node.cost

            # Chấp nhận nếu tốt hơn, hoặc theo xác suất Boltzmann
            if delta < 0 or random.random() < math.exp(-delta / T):
                current_node = next_node

            T *= alpha

        if current_node.state == goal_state:
            return current_node

    return None

def bfs_belief_state(initial_states, goal_state=None, stop_flag=None, max_belief_size=2):
    if goal_state is None:
        goal_state = goal

    belief_list = initial_states[:max_belief_size]

    if all(s == goal_state for s in belief_list):
        return Node(belief_list[0])

    root = Node(belief_list[0])
    root._belief = belief_list 

    frontier = deque([root])
    explored = set()
    explored.add(belief_to_key(belief_list))

    while frontier:
        if stop_flag and stop_flag():
            return None

        node = frontier.popleft()
        current_belief = node._belief

        for action in actions:
            next_belief = [move(s, action) for s in current_belief]

            next_key = belief_to_key(next_belief)
            if next_key in explored:
                continue
            explored.add(next_key)

            child = Node(
                state=next_belief[0],        
                parent=node,
                cost=node.cost + 1,
                action=action,
            )
            child._belief = next_belief

            if all(s == goal_state for s in next_belief):
                return child

            frontier.append(child)

    return None

def and_or_search(initial_belief, goal_state=None, max_depth=100 ,stop_flag=None):

    if goal_state is None:
        goal_state = goal

    return or_search(initial_belief,goal_state,[],0,max_depth)

def or_search(belief_state, goal_state, path, depth, max_depth):
    if all(s == goal_state for s in belief_state):
        return []

    if depth >= max_depth:
        return None

    belief_key = belief_to_key(belief_state)

    if belief_key in path:
        return None

    for action in actions:
        result_states = []
        for state in belief_state:
            child = move(state, action)

            if child != state:
                result_states.append(child)

        if not result_states:
            continue

        plan = and_search(result_states, goal_state, path + [belief_key], depth + 1, max_depth)

        if plan is not None:
            return [action, plan]

    return None

def and_search(states, goal_state, path, depth, max_depth):
    plans = {}

    for state in states:
        plan_s = or_search([state], goal_state, path, depth, max_depth)

        if plan_s is None:
            return None

        plans[to_tuple(state)] = plan_s

    return plans

def get_path(node):
    path = []
    while node.parent is not None:
        path.append((node.action, node.state))
        node = node.parent
    path.append(("Start", node.state))
    path.reverse()
    return path

def h_cost(state, goal_state):
    h = 0
    for i in range(3):
        for j in range(3):

            if state[i][j] == 0:
                continue
            target = state[i][j]
            target_pos = None

            for r in range(3):
                for c in range(3):
                    if goal_state[r][c] == target:
                        target_pos = (r, c)
                        break
                if target_pos:
                    break
            
            h += manhattan((i, j), target_pos)
    return h

def manhattan(x,y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1])

def belief_to_key(belief_states):
    return frozenset(to_tuple(s) for s in belief_states) # Sử dụng frozenset để đảm bảo tính bất biến và không phụ thuộc vào thứ tự

def solve_belief_state_same_goal_bfs(
        start1,
        start2,
        goal1,
        goal2,
        stop_flag=None):

    belief = [start1, start2]

    root = Node(
        state=belief[0],
        belief=belief
    )

    if belief_same_goal_reached(
            belief,
            goal1,
            goal2):
        return root

    frontier = deque([root])

    explored = {
        belief_to_key(belief)
    }

    while frontier:

        if stop_flag and stop_flag():
            return None

        node = frontier.popleft()

        current_belief = node._belief

        for action in actions:

            next_belief = [
                move(s, action)
                for s in current_belief
            ]

            if next_belief == current_belief:
                continue

            next_key = belief_to_key(next_belief)

            if next_key in explored:
                continue

            explored.add(next_key)

            child = Node(
                state=next_belief[0],
                parent=node,
                cost=node.cost + 1,
                action=action,
                belief=next_belief
            )

            if belief_same_goal_reached(
                    next_belief,
                    goal1,
                    goal2):
                return child

            frontier.append(child)

    return None

def plan_to_actions(plan):

    actions_list = []

    while isinstance(plan, list):

        if len(plan) == 0:
            break

        actions_list.append(plan[0])

        if len(plan) < 2:
            break

        subtree = plan[1]

        if not isinstance(subtree, dict):
            break

        first_branch = next(iter(subtree.values()))

        plan = first_branch

    return actions_list


def actions_to_node(initial_state, actions_list):

    root = Node(initial_state)

    current = root
    state = [row[:] for row in initial_state]

    for action in actions_list:

        state = move(state, action)

        current = Node(
            state=state,
            parent=current,
            action=action,
            cost=current.cost + 1
        )

    return current

def belief_same_goal_reached(belief_states, goal1, goal2):
    key = belief_to_key(belief_states)

    return (
        key == belief_to_key([goal1])
        or
        key == belief_to_key([goal2])
    )