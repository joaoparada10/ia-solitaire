from class_solitaire_state import SolitaireState

def greedy(state, visited, cancel_event=None, counter=0):
    # Print progress every 1000 nodes
    if state is None:
        return None
    counter += 1
    if counter % 1000 == 0:
        print(f"Expanded nodes: {counter}")
    
    if cancel_event is not None and cancel_event.is_set():
        return None

    if state.is_goal():
        print(f"Expanded nodes: {counter}")
        return state.moves

    state_repr = represent_state(state)

    if state_repr in visited:
        return None
    visited.add(state_repr)

    current_min = 100000
    next_state = None

    for successor in state.get_successors():
        state_repr_succ = represent_state(successor)
        if state_repr_succ in visited:
            continue
        h_value = heuristic(successor)

        if (h_value < current_min):
            next_state = successor
            current_min = h_value
    
    return greedy(next_state, visited, cancel_event, counter)


# Estimates shortest distance to goal
def heuristic(state):
    # Sum of cards remaining in each tableau column.
    return sum(len(col) for col in state.tableau)

def represent_state(state):
    tableau_str = "|".join(",".join(f"{card.rank}{card.suit}" for card in column) for column in state.tableau)
    foundations_str = "|".join(f"{suit}:{','.join(f'{card.rank}{card.suit}' for card in cards)}" for suit, cards in sorted(state.foundations.items()))
    return f"T:{tableau_str} F:{foundations_str}"
