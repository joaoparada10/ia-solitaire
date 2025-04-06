from class_solitaire_state import SolitaireState
from game import run_dfs_solver, run_greedy_solver, create_deck, deal_cards, run_itd_solver, run_dfs_improved_solver
from astar_solver import AStarSolver
from weighted_astar_solver import WeightedAStarSolver
from constants import SUITS
import pygame
import copy
import time

# 4, 9, 13
# custo(moves), tempo, sucesso

difficulty = 5
num_of_tests = 100
max_useless = 3
depth_limit = 100
a_weight = 1.5

solution = None

dfs_successes = 0
dfs_improved_success = 0
dfs1_successes = 0
dfs1_improved_success = 0
dfs2_successes = 0
dfs2_improved_success = 0

""" dfs_itr_successes = 0 """

a_star_successes = 0
a_star_w_successes = 0

a_star_w1_successes = 0

a_star_w2_successes = 0

greedy_successes = 0

dfs_moves = 0
dfs_improved_moves = 0
dfs1_moves = 0
dfs1_improved_moves = 0
dfs2_moves = 0
dfs2_improved_moves = 0

""" dfs_itr_moves = 0 """

a_star_moves = 0
a_star_w_moves = 0

a_star_w1_moves = 0

a_star_w2_moves = 0

greedy_moves = 0

dfs_time = 0
dfs_improved_time = 0
dfs1_time = 0
dfs1_improved_time = 0
dfs2_time = 0
dfs2_improved_time = 0

""" dfs_itr_time = 0 """

a_star_time = 0
a_star_w_time = 0

a_star_w1_time = 0

a_star_w2_time = 0

greedy_time = 0

for i in range(1,num_of_tests+1, 1):
    deck = create_deck(difficulty)
    tableau = deal_cards(deck, difficulty)
    foundations = {suit: [] for suit in SUITS}
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))

    max_useless = 3
    depth_limit = 100
    #run DFS

    start_time = time.time()

    solution = run_dfs_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs_successes += 1
        dfs_moves += len(solution)
        dfs_time += runtime

    #run DFS improved

    start_time = time.time()

    solution = run_dfs_improved_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs_improved_success += 1
        dfs_improved_moves += len(solution)
        dfs_improved_time += runtime

    max_useless = 10
    depth_limit = 200
    #run DFS

    start_time = time.time()

    solution = run_dfs_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs1_successes += 1
        dfs1_moves += len(solution)
        dfs1_time += runtime

    #run DFS improved

    start_time = time.time()

    solution = run_dfs_improved_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs1_improved_success += 1
        dfs1_improved_moves += len(solution)
        dfs1_improved_time += runtime

    max_useless = 50
    depth_limit = 500
    #run DFS

    start_time = time.time()

    solution = run_dfs_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs2_successes += 1
        dfs2_moves += len(solution)
        dfs2_time += runtime

    #run DFS improved

    start_time = time.time()

    solution = run_dfs_improved_solver(tableau, foundations, depth_limit, None, max_useless)

    runtime = (time.time() - start_time)

    if solution is not None:
        dfs2_improved_success += 1
        dfs2_improved_moves += len(solution)
        dfs2_improved_time += runtime

    

    #run DFS itr

    """ start_time = pygame.time.get_ticks()

    solution = run_itd_solver(tableau, foundations, depht_limit, None, max_useless)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        dfs_itr_successes += 1
        dfs_itr_moves += len(solution)
        dfs_itr_time += runtime """

    #run A*

    start_time = time.time()

    solver = AStarSolver(initial_state)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = (time.time() - start_time)

    if solution is not None:
        a_star_successes += 1
        a_star_moves += len(solution)
        a_star_time += runtime

    a_weight = 1.2
    #run WA*

    start_time = time.time()

    solver = WeightedAStarSolver(initial_state, weight=a_weight)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = (time.time() - start_time)

    if solution is not None:
        a_star_w_successes += 1
        a_star_w_moves += len(solution)
        a_star_w_time += runtime

    a_weight = 1.5

    #run WA*

    start_time = time.time()

    solver = WeightedAStarSolver(initial_state, weight=a_weight)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = (time.time() - start_time)

    if solution is not None:
        a_star_w1_successes += 1
        a_star_w1_moves += len(solution)
        a_star_w1_time += runtime

    a_weight = 2

    #run WA*

    start_time = time.time()

    solver = WeightedAStarSolver(initial_state, weight=a_weight)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = (time.time() - start_time)

    if solution is not None:
        a_star_w2_successes += 1
        a_star_w2_moves += len(solution)
        a_star_w2_time += runtime

    #run Greedy

    start_time = time.time()

    solution = run_greedy_solver(tableau, foundations, None)

    runtime = (time.time() - start_time)

    if solution is not None:
        greedy_successes += 1
        greedy_moves += len(solution)
        greedy_time += runtime

# Statistics
print("DIFFICULTY "+ str(difficulty) + " RESULTS - AVERAGES FOR 100 RANDOM INITIAL STATES \n")
print("DFS Success Rate = " + str(dfs_successes)+"%")
print("DFS Avg Moves = " + f"{dfs_moves / dfs_successes:.4f}")
print("DFS Avg Time = " + f"{dfs_time / dfs_successes:.4f}s" + "\n")


print("DFS Improved Success Rate = " + str(dfs_improved_success)+"%")
print("DFS Improved Avg Moves = " + f"{dfs_improved_moves / dfs_improved_success:.4f}")
print("DFS Improved Avg Time = " + f"{dfs_improved_time / dfs_improved_success:.4f}s" + "\n")

print("DFS1 Success Rate = " + str(dfs1_successes)+"%")
print("DFS1 Avg Moves = " + f"{dfs1_moves / dfs1_successes:.4f}")
print("DFS1 Avg Time = " + f"{dfs1_time / dfs1_successes:.4f}s" + "\n")

print("DFS Improved1 Success Rate = " + str(dfs1_improved_success)+"%")
print("DFS Improved1 Avg Moves = " + f"{dfs1_improved_moves / dfs1_improved_success:.4f}")
print("DFS Improved1 Avg Time = " + f"{dfs1_improved_time / dfs1_improved_success:.4f}s" + "\n")

print("DFS2 Success Rate = " + str(dfs2_successes)+"%")
print("DFS2 Avg Moves = " + f"{dfs2_moves / dfs2_successes:.4f}")
print("DFS2 Avg Time = " + f"{dfs2_time / dfs2_successes:.4f}s" + "\n")

print("DFS Improved2 Success Rate = " + str(dfs2_improved_success)+"%")
print("DFS Improved2 Avg Moves = " + f"{dfs2_improved_moves / dfs2_improved_success:.4f}")
print("DFS Improved2 Avg Time = " + f"{dfs2_improved_time / dfs2_improved_success:.4f}s" + "\n")

""" print("DFS Itr Success Rate = " + str(dfs_itr_successes)+"%")
print("DFS Itr Avg Moves = " + f"{dfs_itr_moves / dfs_itr_successes:.4f}")
print("DFS Itr Avg Time = " + f"{dfs_itr_time / dfs_itr_successes:.4f}s" + "\n") """

print("A Star Success Rate = " + str(a_star_successes)+"%")
print("A Star Avg Moves = " + f"{a_star_moves / a_star_successes:.4f}")
print("A Star Avg Time = " + f"{a_star_time / a_star_successes:.4f}s" + "\n")

print("A Star Weighted Success Rate = " + str(a_star_w_successes)+"%")
print("A Star Weighted Avg Moves = " + f"{a_star_w_moves / a_star_w_successes:.4f}")
print("A Star Weighted Avg Time = " + f"{a_star_w_time / a_star_w_successes:.4f}s" + "\n")

print("A Star Weighted1 Success Rate = " + str(a_star_w_successes)+"%")
print("A Star Weighted1 Avg Moves = " + f"{a_star_w_moves / a_star_w_successes:.4f}")
print("A Star Weighted1 Avg Time = " + f"{a_star_w_time / a_star_w_successes:.4f}s" + "\n")

print("A Star Weighted2 Success Rate = " + str(a_star_w_successes)+"%")
print("A Star Weighted2 Avg Moves = " + f"{a_star_w_moves / a_star_w_successes:.4f}")
print("A Star Weighted2 Avg Time = " + f"{a_star_w_time / a_star_w_successes:.4f}s" + "\n")

print("Greedy Success Rate = " + str(greedy_successes)+"%")
print("Greedy Avg Moves = " + f"{greedy_moves / greedy_successes:.4f}")
print("Greedy Avg Time = " + f"{greedy_time / greedy_successes:.4f}s" + "\n")
