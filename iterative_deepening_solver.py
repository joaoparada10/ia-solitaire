import copy
from dfs_solver import dfs 
from class_solitaire_state import SolitaireState

def iterative_deepening(initial_state, max_depth=100, max_useless=20, cancel_event=None):
    """
    Perform iterative deepening search starting with a depth limit of tableau_size
    and increasing up to max_depth. The max_useless parameter is passed along
    to the DFS function to prune unpromising branches.
    
    Args:
        initial_state (SolitaireState): The starting state of the game.
        max_depth (int): The maximum depth limit to try.
        max_useless (int): The maximum allowed count of non-improving moves.
        cancel_event: Optional threading.Event to cancel the search.
        
    Returns:
        The solution moves (if found), otherwise None.
    """
    for depth in range(initial_state.tableau_size(), max_depth + 1):
        print(f"Trying DFS with depth limit: {depth}")
        # Create a new visited set for each DFS run.
        visited = set()
        # Reset the DFS node counter for each iteration.
        solution, _ = dfs(initial_state, visited, depth, cancel_event, useless_count=0, max_useless=max_useless, counter=[0])
        if solution is not None:
            print(f"Solution found at depth {depth}")
            return solution
    print("No solution found up to the maximum depth limit.")
    return None
