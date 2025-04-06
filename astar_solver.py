import heapq
from constants import RANK_VALUES


class AStarSolver:
    def __init__(self, initial_state):
        self.initial_state = initial_state
        self.nodes_expanded = 0
        
    def solve(self, max_nodes=100000, cancel_event=None):
        open_set = []
        heapq.heappush(open_set, (0, 0, self.initial_state))
        
        came_from = {}
        g_score = {repr(self.initial_state): 0}
        f_score = {repr(self.initial_state): improved_heuristic(self.initial_state)}
        
        open_set_hash = {repr(self.initial_state)}
        tiebreaker = 1
        
        print("Initial state:")
        print(self.initial_state)
        
        while open_set:
            if cancel_event and cancel_event.is_set():
                print("Search cancelled")
                return None, self.nodes_expanded
                
            if self.nodes_expanded >= max_nodes:
                print(f"Reached max nodes ({max_nodes})")
                return None, self.nodes_expanded
                
            current_f, _, current_state = heapq.heappop(open_set)
            open_set_hash.remove(repr(current_state))
            self.nodes_expanded += 1
            
            if self.nodes_expanded % 1000 == 0:
                print(f"\nNodes expanded: {self.nodes_expanded}")
                print(f"Current state (f={current_f}):")
                print(current_state)
                print(f"Open set size: {len(open_set)}")
                print(f"Unique states stored: {len(g_score)}")
            
            if current_state.is_goal():
                print(f"\nSolution found after {self.nodes_expanded} nodes!")
                path = []
                while repr(current_state) in came_from:
                    path.append(current_state.moves[-1])
                    current_state = came_from[repr(current_state)]
                path.reverse()
                return path, self.nodes_expanded
                
            for neighbor in current_state.get_successors():
                neighbor_repr = repr(neighbor)
                tentative_g_score = g_score[repr(current_state)] + current_state.get_cost(neighbor.moves[-1] if neighbor.moves else 0)
                
                if neighbor_repr not in g_score or tentative_g_score < g_score[neighbor_repr]:
                    came_from[neighbor_repr] = current_state
                    g_score[neighbor_repr] = tentative_g_score
                    f_score[neighbor_repr] = tentative_g_score + improved_heuristic(neighbor)
                    if neighbor_repr not in open_set_hash:
                        tiebreaker += 1
                        heapq.heappush(open_set, (f_score[neighbor_repr], tiebreaker, neighbor))
                        open_set_hash.add(neighbor_repr)
                        
        print("No solution found - open set exhausted")
        return None, self.nodes_expanded
    
def improved_heuristic(state):
    remaining_cards = 0
    blocked_cards = 0
    blocking_penalty = 0
    sequence_bonus = 0
    empty_column_bonus = 0
    immovable_penalty = 0

    # Precomputations
    rank_order = ['4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king']
    num_columns = len(state.tableau)
    blocking_rank = rank_order[num_columns - 4] if 4 <= num_columns <= 13 else None

    # Traverse the tableau once
    for col in state.tableau:
        remaining_cards += len(col)
        
        if not col:
            empty_column_bonus -= 5  # Bonus for empty columns
            continue
        
        blocked_cards += len(col) - 1  # All except the top card
        
        # Check penalties and sequences
        for i, card in enumerate(col):
            # Penalty for cards blocking the game
            if blocking_rank and card.rank == blocking_rank and i < len(col) - 1:
                blocking_penalty += (len(col) - i) * 3
            
            # Bonus for sequences of the same suit
            if i < len(col) - 1:
                next_card = col[i + 1]
                if (RANK_VALUES[card.rank] == RANK_VALUES[next_card.rank] + 1 and
                    card.suit == next_card.suit):
                    sequence_bonus -= 2  # Negative bonus (reduces heuristic)
                
                # Penalty for cards blocking sequences
                if RANK_VALUES[card.rank] != RANK_VALUES[next_card.rank] + 1:
                    immovable_penalty += 2

    foundation_progress = sum(len(pile) for pile in state.foundations.values())

    # Final heuristic calculation
    heuristic_value = (
        remaining_cards * 3 +
        blocked_cards * 2 +
        blocking_penalty * 3 +
        sequence_bonus * 1.5 +
        empty_column_bonus +
        immovable_penalty +
        -foundation_progress * 5  # Greater reward
    )
    return heuristic_value
