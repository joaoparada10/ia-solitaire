from class_solitaire_state import SolitaireState
from game import run_dfs_solver, run_greedy_solver, create_deck, deal_cards, run_itd_solver, run_dfs_improved_solver
from astar_solver import AStarSolver
from weighted_astar_solver import WeightedAStarSolver
from constants import SUITS
import pygame
import copy

# 4, 9, 13
# custo(moves), tempo, sucesso

difficulty = 4
num_of_tests = 100
max_useless = 10
depht_limit = 200
a_weight = 1.5

solution = None

dfs_successes = 0
dfs_improved_success = 0
dfs_itr_successes = 0
a_star_successes = 0
a_star_w_successes = 0
greedy_successes = 0

dfs_moves = 0
dfs_improved_moves = 0
dfs_itr_moves = 0
a_star_moves = 0
a_star_w_moves = 0
greedy_moves = 0

dfs_time = 0
dfs_improved_time = 0
dfs_itr_time = 0
a_star_time = 0
a_star_w_time = 0
greedy_time = 0

for i in range(1,num_of_tests+1, 1):
    deck = create_deck(difficulty)
    tableau = deal_cards(deck, difficulty)
    foundations = {suit: [] for suit in SUITS}
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))

    #run DFS

    start_time = pygame.time.get_ticks()

    solution = run_dfs_solver(tableau, foundations, depht_limit, None, max_useless)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        dfs_successes += 1
        dfs_moves += len(solution)
        dfs_time += runtime

    #run DFS improved

    start_time = pygame.time.get_ticks()

    solution = run_dfs_improved_solver(tableau, foundations, depht_limit, None, max_useless)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        dfs_improved_success += 1
        dfs_improved_moves += len(solution)
        dfs_improved_time += runtime

    #run DFS itr

    start_time = pygame.time.get_ticks()

    solution = run_itd_solver(tableau, foundations, depht_limit, None, max_useless)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        dfs_itr_successes += 1
        dfs_itr_moves += len(solution)
        dfs_itr_time += runtime

    #run A*

    start_time = pygame.time.get_ticks()

    solver = AStarSolver(initial_state)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        a_star_successes += 1
        a_star_moves += len(solution)
        a_star_time += runtime

    #run WA*

    start_time = pygame.time.get_ticks()

    solver = WeightedAStarSolver(initial_state, weight=a_weight)
    solution = solver.solve(max_nodes=100000, cancel_event=None)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        a_star_w_successes += 1
        a_star_w_moves += len(solution)
        a_star_w_time += runtime

    #run Greedy

    start_time = pygame.time.get_ticks()

    solution = run_greedy_solver(tableau, foundations, depht_limit, None)

    runtime = pygame.time.get_ticks() - start_time

    if solution is not None:
        greedy_successes += 1
        greedy_moves += len(solution)
        greedy_time += runtime

# Statistics
print("DFS Success Rate = " + str(dfs_successes))
print("DFS Avg Moves = " + str(dfs_moves / dfs_successes))
print("DFS Avg Time = " + str(dfs_time / dfs_successes))

print("DFS Improved Success Rate = " + str(dfs_improved_success))
print("DFS Improved Avg Moves = " + str(dfs_improved_moves / dfs_improved_success))
print("DFS Improved Avg Time = " + str(dfs_improved_time / dfs_improved_success))

print("DFS Itr Success Rate = " + str(dfs_itr_successes))
print("DFS Itr Avg Moves = " + str(dfs_itr_moves / dfs_itr_successes))
print("DFS Itr Avg Time = " + str(dfs_itr_time / dfs_itr_successes))

print("A Star Success Rate = " + str(a_star_successes))
print("A Star Avg Moves = " + str(a_star_moves / a_star_successes))
print("A Star Avg Time = " + str(a_star_time / a_star_successes))

print("A Star Weighted Success Rate = " + str(a_star_w_successes))
print("A Star Weighted Avg Moves = " + str(a_star_w_moves / a_star_w_successes))
print("A Star Weighted Avg Time = " + str(a_star_w_time / a_star_w_successes))

print("Greedy Success Rate = " + str(greedy_successes))
print("Greedy Avg Moves = " + str(greedy_moves / greedy_successes))
print("Greedy Avg Time = " + str(greedy_time / greedy_successes))
