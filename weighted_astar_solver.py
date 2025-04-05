import heapq
from constants import RANK_VALUES

class WeightedAStarSolver:
    def __init__(self, initial_state, weight=1.5):
        self.initial_state = initial_state
        self.nodes_expanded = 0
        self.weight = weight  # The weight parameter for weighted A*
        
    def solve(self, max_nodes=100000, cancel_event=None):
        open_set = []
        # Push (f_score, tiebreaker, state) to the heap
        heapq.heappush(open_set, (0, 0, self.initial_state))
        
        came_from = {}
        g_score = {repr(self.initial_state): 0}
        # Apply weight to heuristic 
        f_score = {repr(self.initial_state): self.weight * improved_heuristic(self.initial_state)}
        
        open_set_hash = {repr(self.initial_state)}
        tiebreaker = 1
        
        print("Initial state:")
        print(self.initial_state)
        
        while open_set:
            if cancel_event and cancel_event.is_set():
                print("Search cancelled")
                return None
                
            if self.nodes_expanded >= max_nodes:
                print(f"Reached max nodes ({max_nodes})")
                return None
                
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
                return path
                
            for neighbor in current_state.get_successors():
                neighbor_repr = repr(neighbor)
                tentative_g_score = g_score[repr(current_state)] + current_state.get_cost(neighbor.moves[-1] if neighbor.moves else 0)
                
                if neighbor_repr not in g_score or tentative_g_score < g_score[neighbor_repr]:
                    came_from[neighbor_repr] = current_state
                    g_score[neighbor_repr] = tentative_g_score
                    # Apply weight to heuristic
                    f_score[neighbor_repr] = tentative_g_score + self.weight * improved_heuristic(neighbor)
                    if neighbor_repr not in open_set_hash:
                        tiebreaker += 1
                        heapq.heappush(open_set, (f_score[neighbor_repr], tiebreaker, neighbor))
                        open_set_hash.add(neighbor_repr)
                        
        print("No solution found - open set exhausted")
        return None
    
def improved_heuristic(state):
    # 1. Count remaining cards in tableau (highest priority)
    remaining_cards = state.tableau_size()

    # 2. Blocked cards (all except top in each column)
    blocked_cards = sum(len(col) - 1 for col in state.tableau if len(col) > 1)

    # 3. Foundation progress (reward moving cards to foundations)
    foundation_progress = sum(len(pile) for pile in state.foundations.values())

    # 4. Dynamic blocking penalty (based on columns)
    blocking_penalty = 0
    rank_order = ['king', 'queen', 'jack', '10', '9', '8', '7', '6', '5', '4']  # Up to 4 columns
    num_columns = len(state.tableau)
    
    if 4 <= num_columns <= 13:  # valid column count
        blocking_rank = rank_order[num_columns - 4]  # Maps 4→'4', 5→'5', ..., 13→'king'
        for col in state.tableau:
            for i, card in enumerate(col[:-1]):  # Skip top card
                if card.rank == blocking_rank:
                    blocking_penalty += (len(col) - i) * 3  # Penalty increases with depth

    # 5. Sequence bonus (rewards in-suit sequences)
    sequence_bonus = 0
    for col in state.tableau:
        if len(col) > 1:
            for i in range(len(col) - 2, -1, -1):
                if (RANK_VALUES[col[i].rank] == RANK_VALUES[col[i + 1].rank] + 1 and
                        col[i].suit == col[i + 1].suit):
                    sequence_bonus -= 2  # Reward sequences

    # 6. Empty column bonus (improves mobility)
    empty_column_bonus = sum(1 for col in state.tableau if not col) * (-5)

    # 7. Immovable penalty (cards blocking sequences)
    immovable_penalty = 0
    for col in state.tableau:
        if len(col) > 2:
            for i in range(len(col) - 2):
                if RANK_VALUES[col[i].rank] != RANK_VALUES[col[i + 1].rank] + 1:
                    immovable_penalty += 2

    # Combined heuristic (weighted sum)
    heuristic_value = (
        remaining_cards * 3 +
        blocked_cards * 2 +
        blocking_penalty * 3 +
        sequence_bonus * 1.5 +
        empty_column_bonus +
        immovable_penalty +
        -foundation_progress * 5  # Biggest reward for foundations
    )
    return heuristic_value
