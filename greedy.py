from class_solitaire_state import SolitaireState
from constants import RANK_VALUES

def greedy(state, visited, cancel_event=None, counter=0):
    # Print progress every 1000 nodes
    if state is None:
        return None, counter
    counter += 1
    if counter % 1000 == 0:
        print(f"Expanded nodes: {counter}")
    
    if cancel_event is not None and cancel_event.is_set():
        return None, counter

    if state.is_goal():
        print(f"Expanded nodes: {counter}")
        return state.moves, counter

    state_repr = represent_state(state)

    if state_repr in visited:
        return None, counter
    visited.add(state_repr)

    current_min = 100000
    next_state = None

    if len(state.moves) == 970:
        return None, counter

    for successor in state.get_successors():
        state_repr_succ = represent_state(successor)
        if state_repr_succ in visited:
            continue
        h_value = heuristic(successor)

        if (h_value < current_min):
            next_state = successor
            current_min = h_value
    
    return greedy(next_state, visited, cancel_event, counter)

def greedy_real_time(state, visited):
    if state is None:
        return (None, visited)

    state_repr = represent_state(state)

    if state_repr in visited:
        return (None, visited)
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
    
    return (next_state, visited)

# Estimates shortest distance to goal
def heuristic(state):
    remaining_cards = 0
    blocked_cards = 0
    foundation_progress = 0
    king_penalty = 0
    sequence_bonus = 0
    immovable_penalty = 0
    ace_on_foundation = 0
    imbalance_penalty = 0
    buried_low_cards_penalty = 0
    empty_column_bonus = 0
    #cicle_penalty = 0

    foundation_lengths = [len(pile) for pile in state.foundations.values()]
    rank_order = ['4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king']
    num_columns = len(state.tableau)
    blocking_rank = rank_order[num_columns - 4] if 4 <= num_columns <= 13 else None
    '''
    window = 20
    to_tableau_counter = 0

    if len(state.moves) >= 20:

        recent_moves = state.moves[-window:]
        moved_cards = set()

        for move in recent_moves:
            if move[0] == "to_tableau":
                _, _, _, rank, suit, _ = move
                moved_cards.add((rank, suit))
                to_tableau_counter += 1

        diversity_score = len(moved_cards)

        # Penalize if there’s little diversity
        # Example: if only 1 or 2 cards are being moved repeatedly

        if to_tableau_counter < window:
            cicle_penalty = 0
        elif diversity_score == 1:
            cicle_penalty = 15  # extreme stagnation
        elif diversity_score == 2:
            cicle_penalty = 10
        elif diversity_score == 3:
            cicle_penalty = 5
        elif diversity_score == 4:
            cicle_penalty = 1
        else:
            cicle_penalty = 0  # good diversity
        '''

    # 3. Foundation progress: Encourages moving cards to foundations

    foundation_progress = sum(foundation_lengths)

    # 7. If there are Aces on top, immediatly take them to the fundations

    for foundation in state.foundations.values():
        for card in foundation:
            if card.rank == 'ace':
                ace_on_foundation -= 20
    
    # 8. Balance between foundations (Minimize the distance between the most advanced foundation and the most delayed foundation)

    if foundation_lengths:
        imbalance_penalty = (max(foundation_lengths) - min(foundation_lengths)) * 2
    else:
        imbalance_penalty = 0

    for col in state.tableau:

        # 10. Gives a bonus for every empty column

        if not col:
            #empty_column_bonus -= 5  # Bonus for empty columns
            continue

        # 1. Count of remaining cards in tableau (highest priority factor)

        remaining_cards += len(col)
        
        # 2. Blocked cards: All cards except the topmost in each column

        if len(col) > 1:
            blocked_cards += len(col)-1

        # 5. Sequence potential: Rewarding suit-based sequences

        if len(col) > 1:
            for i in range(len(col) - 2, -1, -1):
                if (RANK_VALUES[col[i].rank] == RANK_VALUES[col[i + 1].rank] + 1 and
                        col[i].suit == col[i + 1].suit):
                    sequence_bonus -= 2  # Reward suit-based sequences more
                else:
                    break

        # 6. Immovable card penalty: Cards deep in a stack without an exit strategy
        '''
        if len(col) > 2:  # If a column has more than 2 cards
            for i in range(len(col) - 2):
                if col[i].rank == 'queen' and col[i + 1].rank == 'king':  # Bad positioning
                    immovable_penalty += 5  # Heavy penalty for stuck cards
        '''

        # 4. Non movemable King (high penalty for being deeper in columns)

        if col[0].rank == blocking_rank:
            king_penalty += (len(col) -1) * 3
        
        # 9. prioritize low cards to be lifted first

        for i, card in enumerate(col[:-1]):  # not top card
            if card.rank in ['ace', '2']:
                buried_low_cards_penalty += (len(col) - i) * 4

    # Combine factors with optimized weights

    heuristic_value = (
        remaining_cards * 3 +
        blocked_cards * 1.5 +
        king_penalty * 3 +  
        sequence_bonus * 1.5 +
        imbalance_penalty +
        immovable_penalty +
        -foundation_progress * 5 # Strong reward for foundation progress
        + ace_on_foundation
        + buried_low_cards_penalty
        + empty_column_bonus
        #+ cicle_penalty
    )

    return heuristic_value

def represent_state(state):
    tableau_str = "|".join(",".join(f"{card.rank}{card.suit}" for card in column) for column in state.tableau)
    #foundations_str = "|".join(f"{suit}:{','.join(f'{card.rank}{card.suit}' for card in cards)}" for suit, cards in sorted(state.foundations.items()))
    return f"T:{tableau_str}"# F:{foundations_str}"
