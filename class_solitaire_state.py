import copy
from helpers import is_valid_move, is_valid_foundation_move
from constants import RANK_VALUES

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
        last_card_moved = None
        if self.moves:
            last_move = self.moves[-1]
            # For a "to_foundation" move, the tuple is ("to_foundation", src_index, card.rank, card.suit)
            # For a "to_tableau" move, it's ("to_tableau", src_index, tgt_index, card.rank, card.suit, [is_useless])
            if last_move[0] == "to_foundation":
                last_card_moved = (last_move[2], last_move[3])
            elif last_move[0] == "to_tableau":
                last_card_moved = (last_move[3], last_move[4])
        
        # --- Generate foundation moves ---
        for i, col in enumerate(self.tableau):
            if not col:
                continue
            card = col[-1]
            # Skip if this is the same card as last moved.
            if last_card_moved and (card.rank, card.suit) == last_card_moved:
                continue
            for suit, foundation in self.foundations.items():
                if card.suit == suit and is_valid_foundation_move(card, foundation):
                    new_state = copy.deepcopy(self)
                    new_state.tableau[i].pop()
                    new_state.foundations[suit].append(card)
                    new_state.moves.append(("to_foundation", i, card.rank, card.suit))
                    successors.append(new_state)
        
        # --- Generate tableau-to-tableau moves ---
        for i, source in enumerate(self.tableau):
            if not source or len(source) < 2:
                continue  # Cannot move if there's only one card.
            card = source[-1]
            if last_card_moved and (card.rank, card.suit) == last_card_moved:
                continue
            for j, target in enumerate(self.tableau):
                if i == j:
                    continue
                if target and is_valid_move(card, target):
                    # Compute the useless flag:
                    # A move is useless if the card being moved is on top of a card of rank x+1 and the target column's top card is also of rank x+1.
                    below = source[-2]  # The card beneath the one being moved.
                    is_useless = (RANK_VALUES[below.rank] == RANK_VALUES[card.rank] + 1 and
                                RANK_VALUES[target[-1].rank] == RANK_VALUES[card.rank] + 1)
                    new_state = copy.deepcopy(self)
                    new_state.tableau[i].pop()
                    new_state.tableau[j].append(card)
                    new_state.moves.append(("to_tableau", i, j, card.rank, card.suit, is_useless))
                    successors.append(new_state)
        
        return successors

    
    def get_cost(self, move): return 1

    def __str__(self):
        foundation_str = "\n".join(f"{suit}: {[str(c) for c in pile]}" 
                                 for suit, pile in self.foundations.items())
        tableau_str = "\n".join(f"Column {i}: {[str(c) for c in col]}" 
                               for i, col in enumerate(self.tableau))
        return f"Foundations:\n{foundation_str}\n\nTableau:\n{tableau_str}"
    
    def tableau_size(self):
        """
        Returns the total number of cards in the tableau.
        This is a simple helper that sums the lengths of each column.
        """
        return sum(len(col) for col in self.tableau)