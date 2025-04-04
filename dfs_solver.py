import copy
from class_solitaire_state import SolitaireState

def dfs(state, visited, depth_limit, cancel_event=None, useless_count=0, max_useless=20, counter=[0]):
    # Print progress every 1000 nodes
    counter[0] += 1
    if counter[0] % 1000 == 0:
        print(f"Expanded nodes: {counter[0]}, depth_limit: {depth_limit}, current useless: {useless_count}")

    if cancel_event is not None and cancel_event.is_set():
        return None, useless_count
    if state.is_goal():
        print(f"Expanded nodes: {counter[0]}, depth_limit: {depth_limit}, current useless: {useless_count}")
        return state.moves, useless_count
    if depth_limit <= 0:
        return None, useless_count

    state_repr = repr(state)
    if state_repr in visited:
        return None, useless_count
    visited.add(state_repr)

    current_h = heuristic(state)
    for successor in state.get_successors():
        new_h = heuristic(successor)
        # If the successor does not improve the state (i.e. same or higher card count), increase useless_count.
        new_useless = useless_count + 1 if new_h >= current_h else 0
        if new_useless >= max_useless:
            # Prune this branch.
            continue
        result, returned_useless = dfs(successor, visited, depth_limit - 1,
                                         cancel_event, new_useless, max_useless, counter)
        if result is not None:
            return result, returned_useless
    return None, useless_count

def heuristic(state):
    # Sum of cards remaining in each tableau column.
    return state.tableau_size()


def dfs_improved(state, visited, depth_limit, cancel_event=None, useless_count=0, max_useless=20, counter=[0]):
    """
    An improved version of DFS that orders the successors based on the tableau size (or heuristic)
    so that states with fewer cards are explored first.
    """
    counter[0] += 1
    if counter[0] % 1000 == 0:
        print(f"Improved DFS Expanded nodes: {counter[0]}, depth_limit: {depth_limit}, current useless: {useless_count}")

    if cancel_event is not None and cancel_event.is_set():
        return None, useless_count
    if state.is_goal():
        print(f"Improved DFS Expanded nodes: {counter[0]}, depth_limit: {depth_limit}, current useless: {useless_count}")
        return state.moves, useless_count
    if depth_limit <= 0:
        return None, useless_count

    state_repr = repr(state)
    if state_repr in visited:
        return None, useless_count
    visited.add(state_repr)

    current_h = heuristic(state)
    # Order successors: states with a smaller tableau (i.e. lower heuristic value) are tried first.
    successors = state.get_successors()
    current_h = heuristic(state)
    ordered_successors = sorted(
        successors,
        key=lambda s: ((0 if heuristic(s) < current_h else 1), heuristic(s))
    )
    for successor in ordered_successors:
        new_h = heuristic(successor)
        new_useless = useless_count + 1 if new_h >= current_h else 0
        if new_useless >= max_useless:
            continue
        result, returned_useless = dfs_improved(successor, visited, depth_limit - 1,
                                                  cancel_event, new_useless, max_useless, counter)
        if result is not None:
            return result, returned_useless
    return None, useless_count
