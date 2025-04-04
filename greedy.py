from class_solitaire_state import SolitaireState
from constants import RANK_VALUES

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
    # 1. Count of remaining cards in tableau (highest priority factor)
    remaining_cards = sum(len(col) for col in state.tableau)

    # 2. Blocked cards: All cards except the topmost in each column
    blocked_cards = sum(len(col) - 1 for col in state.tableau if len(col) > 1)

    # 3. Foundation progress: Encourages moving cards to foundations
    foundation_progress = sum(len(pile) for pile in state.foundations.values())
    '''
    # 4. Kings blocking movement (high penalty for being deeper in columns)
    king_penalty = 0
    for col in state.tableau:
        for i, card in enumerate(col[:-1]):  # Ignore topmost card
            if card.rank == 'king':
                king_penalty += (len(col) - i) * 3  # Increased penalty
    '''
    # 5. Sequence potential: Rewarding suit-based sequences
    sequence_bonus = 0
    for col in state.tableau:
        if len(col) > 1:
            for i in range(len(col) - 2, -1, -1):
                if (RANK_VALUES[col[i].rank] == RANK_VALUES[col[i + 1].rank] + 1 and
                        col[i].suit == col[i + 1].suit):
                    sequence_bonus -= 2  # Reward suit-based sequences more
                else:
                    break

    # 6. Empty column bonus: Empty columns improve mobility
    #empty_column_bonus = sum(1 for col in state.tableau if not col) * (-5)

    # 7. Immovable card penalty: Cards deep in a stack without an exit strategy
    immovable_penalty = 0
    for col in state.tableau:
        if len(col) > 2:  # If a column has more than 2 cards
            for i in range(len(col) - 2):
                if col[i].rank == 'queen' and col[i + 1].rank == 'king':  # Bad positioning
                    immovable_penalty += 5  # Heavy penalty for stuck cards
    
    # 8. If there are Aces on top, immediatly take them to the fundations
    ace_on_top = 0
    for col in state.tableau:
        if len(col) > 0:
            if col[-1].rank == 'ace':
                ace_on_top += 0

    ace_on_foundation = 0
    for foundation in state.foundations.values():
        for card in foundation:
            if card.rank == 'ace':
                ace_on_foundation -= 15

    # Combine factors with optimized weights
    heuristic_value = (
        remaining_cards * 3 +
        blocked_cards * 2 +
        #king_penalty * 3 +  
        sequence_bonus * 1.5 +
        #empty_column_bonus +
        immovable_penalty +
        -foundation_progress * 5 # Strong reward for foundation progress
        + ace_on_foundation
    )

    return heuristic_value

def represent_state(state):
    tableau_str = "|".join(",".join(f"{card.rank}{card.suit}" for card in column) for column in state.tableau)
    #foundations_str = "|".join(f"{suit}:{','.join(f'{card.rank}{card.suit}' for card in cards)}" for suit, cards in sorted(state.foundations.items()))
    return f"T:{tableau_str}"# F:{foundations_str}"
