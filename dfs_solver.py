import copy
from helpers import is_valid_move, is_valid_foundation_move

class SolitaireState:
    def __init__(self, tableau, foundations, moves=None):
        self.tableau = tableau  # list of lists of cards
        self.foundations = foundations  # dict mapping suit to list of cards
        self.moves = moves if moves is not None else []  # record of moves made

    
    def __repr__(self):
        # Create a canonical representation:
        # Represent each card as a tuple (rank, suit)
        tableau_repr = tuple(tuple((card.rank, card.suit) for card in col) for col in self.tableau)
        # For foundations, sort by suit so the order is consistent.
        foundations_repr = tuple(sorted((suit, tuple((card.rank, card.suit) for card in pile))
                                          for suit, pile in self.foundations.items()))
        return str((tableau_repr, foundations_repr))

    def is_goal(self):
        return all(len(col) == 0 for col in self.tableau)

    def get_successors(self):
        successors = []
        # Determine the card that was moved last, if any.
        last_card_moved = None
        if self.moves:
            last_move = self.moves[-1]
            # Our moves are tuples. For a "to_foundation" move, the tuple is:
            # ("to_foundation", src_index, card.rank, card.suit)
            # For a "to_tableau" move, it's:
            # ("to_tableau", src_index, tgt_index, card.rank, card.suit)
            if last_move[0] == "to_foundation":
                last_card_moved = (last_move[2], last_move[3])
            elif last_move[0] == "to_tableau":
                last_card_moved = (last_move[3], last_move[4])

        # Always generate foundation moves.
        for i, col in enumerate(self.tableau):
            if not col:
                continue
            card = col[-1]
            # If the last move moved the same card, skip this move.
            if last_card_moved and (card.rank, card.suit) == last_card_moved:
                continue
            for suit, foundation in self.foundations.items():
                if card.suit == suit and is_valid_foundation_move(card, foundation):
                    new_state = copy.deepcopy(self)
                    new_state.tableau[i].pop()
                    new_state.foundations[suit].append(card)
                    new_state.moves.append(("to_foundation", i, card.rank, card.suit))
                    successors.append(new_state)

        # For tableau-to-tableau moves, we also check that the move does not move the same card.
        for i, source in enumerate(self.tableau):
            if not source or len(source) < 2:
                continue  # Can't uncover any card if there's only one.
            card = source[-1]
            if last_card_moved and (card.rank, card.suit) == last_card_moved:
                continue
            for j, target in enumerate(self.tableau):
                if i == j:
                    continue
                if target and is_valid_move(card, target):
                    new_state = copy.deepcopy(self)
                    new_state.tableau[i].pop()
                    new_state.tableau[j].append(card)
                    new_state.moves.append(("to_tableau", i, j, card.rank, card.suit))
                    successors.append(new_state)
        return successors
    
    def get_cost(self, move): return 1

    def __str__(self):
        foundation_str = "\n".join(f"{suit}: {[c.rank for c in pile]}" 
                                 for suit, pile in self.foundations.items())
        tableau_str = "\n".join(f"Column {i}: {[c.rank for c in col]}" 
                               for i, col in enumerate(self.tableau))
        return f"Foundations:\n{foundation_str}\n\nTableau:\n{tableau_str}"


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
    return sum(len(col) for col in state.tableau)


