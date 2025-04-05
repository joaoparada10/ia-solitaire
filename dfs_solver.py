import copy
from class_solitaire_state import SolitaireState

def dfs(state, visited, depth_limit, cancel_event=None, useless_count=0, max_useless=20, counter=[0]):
    # Print progress every 1000 nodes.
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
        # Determine if the successor's last move is a tableau move and get its useless flag.
        move_is_useless = False
        if successor.moves and successor.moves[-1][0] == "to_tableau":
            # We expect the tableau move tuple to have an extra flag at index 5.
            if len(successor.moves[-1]) >= 6:
                move_is_useless = successor.moves[-1][5]

        # Compute new_useless based on improvement and the useless flag.
        if new_h < current_h:
            new_useless = 0
        else:
            # new_h is not an improvement (i.e. equal or worse).
            if successor.moves and successor.moves[-1][0] == "to_tableau":
                # For tableau moves, if the move is non-useless, reset the counter; if useless, increment.
                new_useless = 0 if not move_is_useless else useless_count + 1
            else:
                # For non-tableau moves (like moves to the foundation), assume they help and reset.
                new_useless = 0

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
    Improved DFS that orders successors as follows:
      - Priority 1: Moves that reduce the tableau size by exactly one are tried first.
      - Priority 2: Among moves with equal reduction, non-useless tableau moves (i.e. moves that do not move a card
                   that was on top of a card of rank x+1 onto another card of rank x+1) are preferred.
      - Priority 3: Finally, states with a lower tableau size are prioritized.
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
    successors = state.get_successors()
    
    def sort_key(s):
        new_h = heuristic(s)
        # Primary: Check if the move reduces tableau size by exactly one.
        delta = current_h - new_h
        primary = 0 if delta == 1 else 1
        # Secondary: Determine if the last move is a tableau move and, if so, whether it is non-useless.
        if s.moves:
            last_move = s.moves[-1]
            if last_move[0] == "to_tableau":
                # Expecting the move tuple to have an extra flag at index 5.
                # Non-useless move -> flag is False, so secondary key 0; otherwise 1.
                secondary = 0 if len(last_move) >= 6 and not last_move[5] else 1
            else:
                secondary = 0  # For non-tableau moves, treat them as good.
        else:
            secondary = 0
        # Tertiary: Lower tableau size is preferred.
        return (primary, secondary, new_h)
    
    ordered_successors = sorted(successors, key=sort_key)

    for successor in ordered_successors:
        if successor.moves and successor.moves[-1][0] == "to_tableau":
            move_is_useless = successor.moves[-1][5]  # This flag is set in get_successors
            new_useless = useless_count + 1 if move_is_useless else 0
        else:
            # For non-tableau moves (like to_foundation moves), assume they’re beneficial.
            new_useless = 0
        if new_useless >= max_useless:
            continue
        result, returned_useless = dfs_improved(successor, visited, depth_limit - 1,
                                                  cancel_event, new_useless, max_useless, counter)
        if result is not None:
            return result, returned_useless
    return None, useless_count