import pygame
import sys
import random
import copy
from constants import *
from helpers import load_card_images, format_time, is_valid_move, is_valid_foundation_move, has_valid_moves, check_win, update_positions, animate_move, get_hint
from dfs_solver import dfs, dfs_improved
from astar_solver import AStarSolver
from weighted_astar_solver import WeightedAStarSolver
from greedy import greedy, greedy_real_time
from class_solitaire_state import SolitaireState
from iterative_deepening_solver import iterative_deepening
import threading
dfs_cancel_event = threading.Event()

pygame.font.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Baker's Dozen Solitaire")
font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)

CARD_IMAGES = load_card_images()

# --- Card Class ---
class Card:
    def __init__(self, rank, suit, x, y):
        self.rank = rank
        self.suit = suit
        self.image = CARD_IMAGES[(rank, suit)]
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.selected = False
        self.offset_x = 0
        self.offset_y = 0

    def __deepcopy__(self, memo):
        # Create a new Card without deep copying the image.
        new_card = type(self)(self.rank, self.suit, self.rect.x, self.rect.y)
        new_card.selected = self.selected
        new_card.offset_x = self.offset_x
        new_card.offset_y = self.offset_y
        new_card.rect = self.rect.copy()  # Create a copy of the rect.
        # Instead of copying the image, simply assign the reference.
        new_card.image = self.image
        memo[id(self)] = new_card
        return new_card
    
    def __str__(self):
        return f"{self.suit}{self.rank}"


    def draw(self, screen):
        pygame.draw.rect(screen, CARD_COLOR, self.rect)
        screen.blit(self.image, (self.rect.x, self.rect.y))

# --- Deck and Dealing ---
def create_deck(difficulty=13):
    return [Card(rank, suit, 0, 0) for suit in SUITS for rank in RANKS[:difficulty]]

def deal_cards(deck, difficulty=13):
    if difficulty == 13:
        tableau = [[] for _ in range(13)]
        kings = [card for card in deck if card.rank == 'king']
        non_kings = [card for card in deck if card.rank != 'king']
        random.shuffle(non_kings)
        king_piles = random.sample(range(13), 4)
        for pile in king_piles:
            tableau[pile].insert(0, kings.pop())
        for i in range(13):
            if i in king_piles:
                for _ in range(3):
                    tableau[i].append(non_kings.pop())
            else:
                for _ in range(4):
                    tableau[i].append(non_kings.pop())
    else:
        columns = difficulty
        tableau = [[] for _ in range(columns)]
        highest_rank = RANKS[difficulty - 1]
        highest_cards = [card for card in deck if card.rank == highest_rank]
        non_highest = [card for card in deck if card.rank != highest_rank]
        random.shuffle(non_highest)
        chosen_columns = random.sample(range(columns), 4) if columns >= 4 else list(range(columns))
        for i in range(columns):
            if i in chosen_columns:
                tableau[i].append(highest_cards.pop())
                for _ in range(3):
                    tableau[i].append(non_highest.pop())
            else:
                for _ in range(4):
                    tableau[i].append(non_highest.pop())
    for col_index, col in enumerate(tableau):
        for card_index, card in enumerate(col):
            card.rect.x = SPACING_X * col_index + 20
            card.rect.y = TABLEAU_Y + card_index * 30
    return tableau

# --- Drawing ---
def draw_table(screen, tableau, foundations, remaining_time, score, undo_count, 
              hint_active=False, hint_card=None, is_human=False):
    screen.fill(BACKGROUND_COLOR)
    for i, col in enumerate(tableau):
        x = SPACING_X * i + 20
        y = TABLEAU_Y + 30
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        if not col:
            pygame.draw.rect(screen, (255,255,255), rect, 3)
    for col in tableau:
        for card in col:
            card.draw(screen)
    for i, suit in enumerate(SUITS):
        x = WIDTH - (4 - i) * SPACING_X
        rect = pygame.Rect(x, FOUNDATION_Y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(screen, (255,255,255), rect, 3)
        if foundations[suit]:
            foundations[suit][-1].rect.x = x
            foundations[suit][-1].rect.y = FOUNDATION_Y
            foundations[suit][-1].draw(screen)
    
    # Draw UI elements
    time_text = font.render(f"Time: {format_time(remaining_time)}", True, TEXT_COLOR)
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(time_text, (20, 20))
    screen.blit(score_text, (20, 50))
    
    # Draw buttons
    return_to_menu_button_rect = pygame.Rect(20, HEIGHT - 50, 170, 40)
    pygame.draw.rect(screen, BUTTON_COLOR, return_to_menu_button_rect)
    return_to_menu_text = font.render("Return to Menu", True, TEXT_COLOR)
    screen.blit(return_to_menu_text, (25, HEIGHT - 45))
    
    
    # Only draw hint and undo button in human mode
    hint_button_rect = None
    if is_human:
        undo_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, 100, 30)
        pygame.draw.rect(screen, BUTTON_COLOR, undo_button_rect)
        undo_text = font.render(f"Undo ({undo_count})", True, TEXT_COLOR)
        screen.blit(undo_text, (WIDTH - 140, HEIGHT - 45))
        hint_button_rect = pygame.Rect(WIDTH - 300, HEIGHT - 50, 100, 30)
        pygame.draw.rect(screen, BUTTON_COLOR, hint_button_rect)
        hint_text = font.render("Hint", True, TEXT_COLOR)
        screen.blit(hint_text, (hint_button_rect.x + 10, hint_button_rect.y + 5))
    
    # Highlight hinted card if active
    if hint_active and hint_card:
        pygame.draw.rect(screen, HINT_COLOR, hint_card.rect, 3)
    
    pygame.display.flip()
    return hint_button_rect  # Return the rect for click detection (None in AI mode)

# --- End Game Screens ---
def game_over_screen(score, moves, solve_time, reason):
    game_over_running = True
    buttons = {
        "Return to Menu": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50),
        "Play Again": pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 140, 200, 50)
    }
    while game_over_running:
        screen.fill(BACKGROUND_COLOR)
        if reason == "time_up":
            game_over_text = font.render("Time's up! Game over.", True, TEXT_COLOR)
        elif reason == "no_valid_moves":
            game_over_text = font.render("No valid moves left! Game over.", True, TEXT_COLOR)
        elif reason == "repeating_moves":
            game_over_text = font.render("Repeated moves detected! Game over.", True, TEXT_COLOR)
        elif reason == "user_won":
            game_over_text = font.render("Congratulations! You won!", True, TEXT_COLOR)
        elif reason == "no_solution":
            game_over_text = font.render("No Solution Found.", True, TEXT_COLOR)
        else:
        
            game_over_text = font.render("Game over.", True, TEXT_COLOR)
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))
        score_text = font.render(f"Total Score: {score}", True, TEXT_COLOR)
        moves_text = font.render(f"Moves: {moves}", True, TEXT_COLOR)
        time_text = font.render(f"Time: {format_time(solve_time)}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 50))
        screen.blit(moves_text, (WIDTH//2 - moves_text.get_width()//2, HEIGHT//2 - 20))
        screen.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2 + 10))
        for text, rect in buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            label = font.render(text, True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        return "menu" if text == "Return to Menu" else "play_again"

# --- Read From Files ---

def parse_card(card_str, x=0, y=0):
    # Example input: "spades4"
    for suit in ["'hearts", "'diamonds", "'clubs", "'spades"]:
        print("Suit:    ")
        print(suit)
        print(card_str)
        print("{card_str}".startswith("{suit}"))
        if str(card_str).startswith(str(suit)):
            print(suit)
            rank = card_str[len(suit):len(card_str)-1]
            return Card(rank, suit[1:], x, y)
    raise ValueError(f"Invalid card string: {card_str}")

def load_state_from_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    tableau = [[] for _ in range(13)]  # max 13 columns
    foundations = {'hearts': [], 'diamonds': [], 'clubs': [], 'spades': []}

    reading_foundations = False
    reading_tableau = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("Foundations:"):
            reading_foundations = True
            reading_tableau = False
            continue
        elif line.startswith("Tableau:"):
            reading_tableau = True
            reading_foundations = False
            continue

        if reading_foundations:
            if ":" in line:
                suit, card_list_str = line.split(":")
                suit = suit.strip()
                card_list_str = card_list_str.strip().strip("[]")
                cards = [parse_card(c.strip()) for c in card_list_str.split(",") if c.strip()]
                foundations[suit] = cards

        elif reading_tableau:
            if line.startswith("Column"):
                col_num_str, card_list_str = line.split(":")
                col_index = int(col_num_str.strip().split(" ")[1])
                card_list_str = card_list_str.strip().strip("[]")
                cards = [parse_card(c.strip()) for c in card_list_str.split(",") if c.strip()]
                tableau[col_index] = cards

    tableau = [col for col in tableau if col]

    for col_index, col in enumerate(tableau):
        for card_index, card in enumerate(col):
            card.rect.x = SPACING_X * col_index + 20
            card.rect.y = TABLEAU_Y + card_index * 30

    return tableau, foundations

# --- DFS Integration ---
def run_dfs_solver(tableau, foundations, depth_limit, cancel_event=None, max_useless=MAX_USELESS_MOVES):
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
    solution, useless = dfs(initial_state, set(), depth_limit, cancel_event, 0, max_useless)
    return solution

def run_dfs_improved_solver(tableau, foundations, depth_limit, cancel_event=None, max_useless=MAX_USELESS_MOVES):
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
    solution, useless = dfs_improved(initial_state, set(), depth_limit, cancel_event, 0, max_useless)
    return solution


# --- Iterative Deepening Integration ---
def run_itd_solver(tableau, foundations, depth_limit, cancel_event=None, max_useless=MAX_USELESS_MOVES):
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
    result = iterative_deepening(initial_state, depth_limit, max_useless, cancel_event)
    if result is None:
        solution, useless = None, None
    else:
        solution, useless = result
    return solution

# --- Greedy Integration ---
def run_greedy_solver(tableau, foundations, cancel_event=None):
    initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
    solution = greedy(initial_state, set(), cancel_event=cancel_event)
    return solution

# --- AI and Human Game Loops & Menus ---
def compute_ai_move(tableau, foundations, algorithm, visited):
    if algorithm == "Simple":
        # Simple AI: first try moving a tableau card to its foundation.
        for col in tableau:
            if col:
                card = col[-1]
                for suit, foundation_pile in foundations.items():
                    if is_valid_foundation_move(card, foundation_pile):
                        return ("to_foundation", card, col, foundation_pile), visited
        for source_col in tableau:
            if source_col:
                card = source_col[-1]
                for target_col in tableau:
                    if source_col == target_col:
                        continue
                    if target_col and is_valid_move(card, target_col):
                        return ("to_tableau", card, source_col, target_col), visited
        return None, visited
    elif algorithm == "Random":
        moves = []
        for col in tableau:
            if col:
                card = col[-1]
                for suit, foundation_pile in foundations.items():
                    if is_valid_foundation_move(card, foundation_pile):
                        moves.append(("to_foundation", card, col, foundation_pile))
        for source_col in tableau:
            if source_col:
                card = source_col[-1]
                for target_col in tableau:
                    if source_col == target_col:
                        continue
                    if target_col and is_valid_move(card, target_col):
                        moves.append(("to_tableau", card, source_col, target_col))
        if moves:
            chosen_move = random.choice(moves)
            return chosen_move, visited
        else:
            return None, visited
    elif algorithm == "Greedy":
        current_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
        next_state, visited = greedy_real_time(current_state,visited)
        move = None
        if next_state is not None:
            move = next_state.moves[-1]
        else:
            return None, visited
        next_move = None
        if move[0] == "to_tableau":
            next_move = ("to_tableau", tableau[move[1]][-1], tableau[move[1]], tableau[move[2]])
        elif move[0] == "to_foundation":
            card = tableau[move[1]][-1]
            for suit, foundation in foundations.items():
                if card.suit == suit:
                    next_move = ("to_foundation", card, tableau[move[1]], foundation)
                    break
        return next_move, visited
    return None, visited

def game_loop(difficulty=13, game_duration=12, tableau=None, read_from_file=False):
    foundations = {suit: [] for suit in SUITS}
    if tableau == None:
        if not read_from_file:
            deck = create_deck(difficulty)
            tableau = deal_cards(deck, difficulty)
        else:
            tableau, foundations = load_state_from_file("initial.txt")
    initial_tableau = copy.deepcopy(tableau)
    running = True
    selected_card = None
    original_position = None
    source_col = None

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    total_time = game_duration * 60 * 1000
    moves_count = 0
    score = 0
    undo_stack = []
    undo_count = 3
    last_click_time = 0
    last_clicked_card = None
    recent_moves = []

    # Hint system variables
    hint_button_rect = pygame.Rect(WIDTH - 300, HEIGHT - 50, 100, 30)  
    hint_active = False
    hint_card = None
    hint_timer = 0

    while running:
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_time = max(total_time - elapsed_time, 0)

        # Check win/lose conditions
        if remaining_time <= 0:
            running = False
            action = game_over_screen(score, moves_count, elapsed_time, "time_up")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                player_mode_menu(initial_tableau)
            return

        if check_win(tableau):
            running = False
            action = game_over_screen(score, moves_count, elapsed_time, "user_won")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                player_mode_menu(initial_tableau)
            return

        if not has_valid_moves(tableau, foundations):
            running = False
            action = game_over_screen(score, moves_count, elapsed_time, "no_valid_moves")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                player_mode_menu(initial_tableau)
            return

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Return to menu button
                return_to_menu_button = pygame.Rect(20, HEIGHT - 50, 170, 40)
                if return_to_menu_button.collidepoint(event.pos):
                    running = False
                    main_menu()
                    return
                
                # Undo button
                undo_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, 100, 30)
                if undo_button_rect.collidepoint(event.pos) and undo_count > 0:
                    if undo_stack:
                        tableau, foundations, score, card_positions = undo_stack.pop()
                        for col in tableau:
                            for card in col:
                                card.rect.x, card.rect.y = card_positions[id(card)]
                        for i, suit in enumerate(SUITS):
                            if foundations[suit]:
                                foundations[suit][-1].rect.x = WIDTH - (4 - i) * SPACING_X
                                foundations[suit][-1].rect.y = FOUNDATION_Y
                        undo_count -= 1
                
                # Hint button
                if hint_button_rect and hint_button_rect.collidepoint(event.pos):
                    hint = get_hint(tableau, foundations)
                    if hint:
                        hint_active = True
                        hint_card = hint[1]  # The card to highlight
                        hint_timer = pygame.time.get_ticks()
                    else:
                        # Show "no hint" message temporarily
                        no_hint_text = font.render("No moves available!", True, (255, 0, 0))
                        screen.blit(no_hint_text, (WIDTH//2 - 80, HEIGHT - 100))
                        pygame.display.flip()
                        pygame.time.delay(1000)
                
                # Card selection
                current_time = pygame.time.get_ticks()
                for col in tableau:
                    if col:
                        card = col[-1]
                        if card.rect.collidepoint(event.pos):
                            if last_clicked_card == card and (current_time - last_click_time) < DOUBLE_CLICK_THRESHOLD:
                                source_col = col
                                card_positions = {id(card): (card.rect.x, card.rect.y) for col in tableau for card in col}
                                undo_stack.append(([c.copy() for c in tableau],
                                                {s: pile.copy() for s, pile in foundations.items()},
                                                score, card_positions))
                                for suit, foundation_pile in foundations.items():
                                    if suit == card.suit and is_valid_foundation_move(card, foundation_pile):
                                        source_col.remove(card)
                                        foundation_pile.append(card)
                                        moves_count += 1
                                        score += SCORE_INCREMENT
                                        source_index = tableau.index(source_col)
                                        move_tuple = ("foundation", card.rank, card.suit, source_index, SUITS.index(suit))
                                        recent_moves.append(move_tuple)
                                        break
                                last_click_time = 0
                                last_clicked_card = None
                                break
                            else:
                                selected_card = card
                                original_position = (card.rect.x, card.rect.y)
                                card.offset_x = event.pos[0] - card.rect.x
                                card.offset_y = event.pos[1] - card.rect.y
                                card_positions = {id(card): (card.rect.x, card.rect.y) for col in tableau for card in col}
                                undo_stack.append(([col.copy() for col in tableau],
                                                {s: pile.copy() for s, pile in foundations.items()},
                                                score, card_positions))
                                last_clicked_card = card
                                last_click_time = current_time
                                break
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_card:
                    selected_card.rect.x = event.pos[0] - selected_card.offset_x
                    selected_card.rect.y = event.pos[1] - selected_card.offset_y
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_card:
                    source_col = None
                    for col in tableau:
                        if col and col[-1] == selected_card:
                            source_col = col
                            break
                    
                    target_col = None
                    for col in tableau:
                        if col and col[-1].rect.collidepoint(event.pos) and source_col != col:
                            target_col = col
                            break
                        elif not col:
                            col_index = tableau.index(col)
                            col_x = SPACING_X * col_index + 20
                            col_rect = pygame.Rect(col_x, TABLEAU_Y + 30, CARD_WIDTH, CARD_HEIGHT)
                            if col_rect.collidepoint(event.pos):
                                target_col = col
                                break
                    
                    moved_to_foundation = False
                    for suit, foundation_pile in foundations.items():
                        if foundation_pile:
                            if foundation_pile[-1].rect.collidepoint(event.pos) and is_valid_foundation_move(selected_card, foundation_pile):
                                source_col.remove(selected_card)
                                foundation_pile.append(selected_card)
                                moves_count += 1
                                score += SCORE_INCREMENT
                                moved_to_foundation = True
                                source_index = tableau.index(source_col)
                                move_tuple = ("foundation", selected_card.rank, selected_card.suit, source_index, SUITS.index(suit))
                                recent_moves.append(move_tuple)
                                break
                        else:
                            foundation_x = WIDTH - (4 - list(foundations.keys()).index(suit)) * SPACING_X
                            foundation_rect = pygame.Rect(foundation_x, FOUNDATION_Y, CARD_WIDTH, CARD_HEIGHT)
                            if foundation_rect.collidepoint(event.pos) and selected_card.rank == 'ace':
                                source_col.remove(selected_card)
                                foundation_pile.append(selected_card)
                                moves_count += 1
                                score += SCORE_INCREMENT
                                moved_to_foundation = True
                                source_index = tableau.index(source_col)
                                move_tuple = ("foundation", selected_card.rank, selected_card.suit, source_index, SUITS.index(suit))
                                recent_moves.append(move_tuple)
                                break
                    
                    if selected_card and not moved_to_foundation:
                        if target_col and is_valid_move(selected_card, target_col):
                            old_top_card = target_col[-1]
                            selected_card.rect.x = old_top_card.rect.x
                            selected_card.rect.y = old_top_card.rect.y + 30
                            source_col.remove(selected_card)
                            target_col.append(selected_card)
                            moves_count += 1
                            source_index = tableau.index(source_col)
                            target_index = tableau.index(target_col)
                            move_tuple = ("tableau", selected_card.rank, selected_card.suit, source_index, target_index)
                            recent_moves.append(move_tuple)
                        else:
                            selected_card.rect.x, selected_card.rect.y = original_position
                            if undo_stack:
                                undo_stack.pop()
                    
                    selected_card = None
                    original_position = None

        # Check for repeating moves
        if len(recent_moves) >= 6:
            m1, m2, m3, m4, m5, m6 = recent_moves[-6:]
            if m1 == m3 == m5 and m2 == m4 == m6:
                running = False
                action = game_over_screen(score, moves_count, elapsed_time,"repeating_moves")
                if action == "menu":
                    main_menu()
                elif action == "play_again":
                    player_mode_menu(initial_tableau)
                return

        # Auto-hide hint after 3 seconds
        if hint_active and pygame.time.get_ticks() - hint_timer > 3000:
            hint_active = False
            hint_card = None

        # Draw everything
        draw_table(screen, tableau, foundations, remaining_time, score, undo_count, 
                            hint_active, hint_card,is_human=True)
        
        # Draw hint button (must be drawn after the cards)
        pygame.draw.rect(screen, BUTTON_COLOR, hint_button_rect)
        hint_text = font.render("Hint", True, TEXT_COLOR)
        screen.blit(hint_text, (hint_button_rect.x + 10, hint_button_rect.y + 5))
        
        # Highlight hinted card if active
        if hint_active and hint_card:
            pygame.draw.rect(screen, HINT_COLOR, hint_card.rect, 3)
        
        pygame.display.flip()
        clock.tick(60)

def ai_game_loop(algorithm, difficulty, game_duration, display_mode, max_useless, depth_limit, weight=1.5,tableau=None, read_from_file=False):
    foundations = {suit: [] for suit in SUITS}
    if tableau == None:
        if not read_from_file:
            deck = create_deck(difficulty)
            tableau = deal_cards(deck, difficulty)
        else:
            tableau, foundations = load_state_from_file("initial.txt")
    initial_tableau = copy.deepcopy(tableau)
    foundations = {suit: [] for suit in SUITS}
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    total_time = game_duration * 60 * 1000
    moves_count = 0
    score = 0
    dfs_cancel_event = threading.Event()
    recent_moves = []
    
    if algorithm in ["DFS", "DFS Improved", "Iterative Deepening", "A*", "Weighted A*"]:
        # Draw initial state
        draw_table(screen, tableau, foundations, total_time, score, undo_count=0, is_human=False)
        
        # Set up UI elements
        searching_text = font.render(f"AI is searching for a solution ({algorithm})...", True, TEXT_COLOR)
        screen.blit(searching_text, (WIDTH//2 - searching_text.get_width()//2, 80))
        
        give_up_rect = pygame.Rect(WIDTH - 200, HEIGHT - 50, 180, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, give_up_rect)
        give_up_text = font.render("Give Up", True, TEXT_COLOR)
        screen.blit(give_up_text, (give_up_rect.x + 10, give_up_rect.y + 5))
        pygame.display.flip()

        solution_container = {}
        
        def solver_thread():
            initial_state = SolitaireState(copy.deepcopy(tableau), copy.deepcopy(foundations))
            
            if algorithm == "DFS":
                solution = run_dfs_solver(tableau, foundations, depth_limit, 
                                         cancel_event=dfs_cancel_event, max_useless=max_useless)
            elif algorithm == "DFS Improved":
                solution = run_dfs_improved_solver(tableau, foundations, depth_limit, cancel_event=dfs_cancel_event, max_useless=max_useless)
            elif algorithm == "Iterative Deepening":
                solution = run_itd_solver(tableau, foundations, depth_limit, 
                                         cancel_event=dfs_cancel_event, max_useless=max_useless)
            elif algorithm == "A*":
                solver = AStarSolver(initial_state)
                solution = solver.solve(max_nodes=100000, cancel_event=dfs_cancel_event)
            elif algorithm == "Weighted A*":
                solver = WeightedAStarSolver(initial_state, weight=weight)
                solution = solver.solve(max_nodes=100000, cancel_event=dfs_cancel_event)
            
            solution_container['solution'] = solution
            if algorithm in ["A*", "Weighted A*"]:
                solution_container['nodes_expanded'] = solver.nodes_expanded

        thread = threading.Thread(target=solver_thread)
        thread.start()

        searching = True
        while searching:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    dfs_cancel_event.set()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if give_up_rect.collidepoint(event.pos):
                        dfs_cancel_event.set()
                        searching = False
                        ai_options_menu(initial_tableau)
                        return

            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            runtime_text = font.render(f"Run Time: {elapsed//1000} sec", True, TEXT_COLOR)
            
            draw_table(screen, tableau, foundations, max(total_time - elapsed, 0), score, undo_count=0, is_human=False)
            screen.blit(searching_text, (WIDTH//2 - searching_text.get_width()//2, 80))
            screen.blit(runtime_text, (WIDTH//2 - runtime_text.get_width()//2, 120))
            
            if algorithm in ["A*", "Weighted A*"] and 'nodes_expanded' in solution_container:
                nodes_text = font.render(f"Nodes expanded: {solution_container['nodes_expanded']}", True, TEXT_COLOR)
                screen.blit(nodes_text, (WIDTH//2 - nodes_text.get_width()//2, 160))
            
            pygame.draw.rect(screen, BUTTON_COLOR, give_up_rect)
            screen.blit(give_up_text, (give_up_rect.x + 10, give_up_rect.y + 5))
            pygame.display.flip()
            clock.tick(30)

            if not thread.is_alive():
                searching = False

        solution = solution_container.get('solution', None)
        runtime = pygame.time.get_ticks() - start_time
        
        if solution:
            print(f"{algorithm} solution found in {runtime}ms")

            # Set duration based on display_mode:
            duration_val = 1000 if display_mode else 10  # 1 sec in slow mode, 10ms in fast mode
            if algorithm in ["A*", "Weighted A*"]:
                print(f"Expanded {solution_container['nodes_expanded']} nodes")
            
            for move in solution:
                if move[0] == "to_foundation":
                    src_index = move[1]
                    card = None
                    for c in tableau[src_index]:
                        if c.rank == move[2] and c.suit == move[3]:
                            card = c
                            break
                    if card is not None:
                        start_pos = (card.rect.x, card.rect.y)
                        foundation_index = SUITS.index(card.suit)
                        target_pos = (WIDTH - (4 - foundation_index) * SPACING_X, FOUNDATION_Y)
                        animate_move(card, start_pos, target_pos, duration=duration_val, 
            draw_func=draw_table, clock=clock,
            extra_draw_args=(screen, tableau, foundations,
                           max(total_time - (pygame.time.get_ticks() - start_time), 0),
                           score, 0, False, None, False))  # hint_active=False, hint_card=None, is_human=False

                        tableau[src_index].pop()
                        foundations[card.suit].append(card)
                        score += SCORE_INCREMENT
                        moves_count += 1

                elif move[0] == "to_tableau":
                    src_index = move[1]
                    tgt_index = move[2]
                    card = None
                    for c in tableau[src_index]:
                        if c.rank == move[3] and c.suit == move[4]:
                            card = c
                            break
                    if card is not None:
                        start_pos = (card.rect.x, card.rect.y)
                        target_x = SPACING_X * tgt_index + 20
                        target_y = TABLEAU_Y + len(tableau[tgt_index]) * 30
                        animate_move(card, start_pos, (target_x, target_y), duration=duration_val,
                                    draw_func=draw_table, clock=clock,
                                    extra_draw_args=(screen, tableau, foundations,
                                                    max(total_time - (pygame.time.get_ticks() - start_time), 0),
                                                    score, 0))
                        tableau[src_index].pop()
                        tableau[tgt_index].append(card)
                        moves_count += 1

                update_positions(tableau)
            action = game_over_screen(score, moves_count, runtime,"user_won")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                ai_options_menu(tableau=initial_tableau)
            return
            
        else:
            action = game_over_screen(score, moves_count, runtime,"no_solution")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                ai_options_menu(tableau=initial_tableau)
        return
    
        '''
        elif algorithm == "Greedy":
            # Display the initial state and a message that Greedy is searching
            draw_table(screen, tableau, foundations, total_time, score, undo_count=0, is_human=False)
            searching_text = font.render("AI is searching for a solution...", True, TEXT_COLOR)
            screen.blit(searching_text, (WIDTH//2 - searching_text.get_width()//2, 80))
            give_up_rect = pygame.Rect(WIDTH - 200, HEIGHT - 50, 180, 40)
            pygame.draw.rect(screen, BUTTON_COLOR, give_up_rect)
            give_up_text = font.render("Give Up", True, TEXT_COLOR)
            screen.blit(give_up_text, (give_up_rect.x + 10, give_up_rect.y + 5))
            pygame.display.flip()

            # Run Greedy in a separate thread.
            solution_container = {}  # Use a dict to store the solution result
            def greedy_thread():
                solution = run_greedy_solver(tableau=tableau, foundations=foundations, cancel_event=dfs_cancel_event)

                solution_container['solution'] = solution

            thread = threading.Thread(target=greedy_thread)
            thread.start()

            # Now enter a loop that updates the display and checks for "Give up"
            searching = True
            while searching:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        dfs_cancel_event.set()
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if give_up_rect.collidepoint(event.pos):
                            # User clicked "Give up"
                            dfs_cancel_event.set()
                            searching = False
                            ai_options_menu(initial_tableau)
                            return

                #update runtime info on screen:
                current_time = pygame.time.get_ticks()
                elapsed = current_time - start_time
                runtime_text = font.render(f"Run Time: {elapsed//1000} sec", True, TEXT_COLOR)
                # Redraw background, initial state, and runtime:
                draw_table(screen, tableau, foundations, max(total_time - elapsed, 0), score, undo_count=0, is_human=False)
                screen.blit(searching_text, (WIDTH//2 - searching_text.get_width()//2, 80))
                screen.blit(runtime_text, (WIDTH//2 - runtime_text.get_width()//2, 120))
                pygame.draw.rect(screen, BUTTON_COLOR, give_up_rect)
                screen.blit(give_up_text, (give_up_rect.x + 10, give_up_rect.y + 5))
                pygame.display.flip()
                clock.tick(30)

                # If the Greedy thread is finished, break out of the loop.
                if not thread.is_alive():
                    searching = False

            # Once Greedy thread finishes, check if we have a solution.
            solution = solution_container.get('solution', None)
            runtime = pygame.time.get_ticks() - start_time
            print("Greedy run time (ms):", runtime)
            if solution is not None:
                print("Greedy solution found:", solution)
                # For each move in the solution, animate it.
                for move in solution:
                    if move[0] == "to_foundation":
                        src_index = move[1]
                        card = None
                        for c in tableau[src_index]:
                            if c.rank == move[2] and c.suit == move[3]:
                                card = c
                                break
                        if card is not None:
                            start_pos = (card.rect.x, card.rect.y)
                            # Determine target position in the foundation.
                            # (Assuming foundation positions are computed as in draw_table)
                            foundation_index = SUITS.index(card.suit)
                            target_pos = (WIDTH - (4 - foundation_index) * SPACING_X, FOUNDATION_Y)
                            # Set duration based on display_mode:
                            duration_val = 1000 if display_mode else 10  # 1 sec in slow mode, 10ms in fast mode
                            animate_move(card, start_pos, target_pos, duration=duration_val, 
                                        draw_func=draw_table, clock=clock,
                                        extra_draw_args=(screen, tableau, foundations,
                                                        max(total_time - (pygame.time.get_ticks() - start_time), 0),
                                                        score, 0))

                            tableau[src_index].pop()
                            foundations[card.suit].append(card)
                            score += SCORE_INCREMENT
                            moves_count += 1

                    elif move[0] == "to_tableau":
                        src_index = move[1]
                        tgt_index = move[2]
                        card = None
                        for c in tableau[src_index]:
                            if c.rank == move[3] and c.suit == move[4]:
                                card = c
                                break
                        if card is not None:
                            start_pos = (card.rect.x, card.rect.y)
                            # Determine target position in the target column.
                            target_x = SPACING_X * tgt_index + 20
                            target_y = TABLEAU_Y + len(tableau[tgt_index]) * 30
                            animate_move(card, start_pos, (target_x, target_y), duration=1000,
                                        draw_func=draw_table, clock=clock,
                                        extra_draw_args=(screen, tableau, foundations,
                                                        max(total_time - (pygame.time.get_ticks() - start_time), 0),
                                                        score, 0))
                            tableau[src_index].pop()
                            tableau[tgt_index].append(card)
                            moves_count += 1

                    # Update positions after each move (optional if animate_move fully controls card positions).
                    update_positions(tableau)
                action = game_over_screen(score, moves_count, runtime, reason="user_won")
            else:
                print("Could not find solution.")
                action = game_over_screen(score, moves_count, runtime, reason="no_solution")
            return
        '''
    else:
        running = True
        visited = set()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    return_to_menu_button = pygame.Rect(20, HEIGHT - 50, 170, 40)
                    if return_to_menu_button.collidepoint(event.pos):
                        running = False
                        main_menu()
                        return

            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - start_time
            remaining_time = max(total_time - elapsed_time, 0)

            if check_win(tableau):
                running = False
                action = game_over_screen(score, moves_count, elapsed_time, reason="user_won")
                if action == "menu":
                    main_menu()
                elif action == "play_again":
                    ai_options_menu(tableau=initial_tableau)
                return

            if remaining_time <= 0 or not has_valid_moves(tableau, foundations):
                running = False
                action = game_over_screen(score, moves_count, elapsed_time, 
                                        reason="time_up" if remaining_time <= 0 else "no_valid_moves")
                if action == "menu":
                    main_menu()
                elif action == "play_again":
                    ai_options_menu(tableau=initial_tableau)
                return

            move, visited = compute_ai_move(tableau, foundations, algorithm, visited)
            if move is None:
                running = False
                action = game_over_screen(score, moves_count, elapsed_time, reason="no_valid_moves")
                if action == "menu":
                    main_menu()
                elif action == "play_again":
                    ai_options_menu(tableau=initial_tableau)
                return

            duration_val = 1000 if display_mode else 10
            move_type, card, source_col, target = move
            if move_type == "to_foundation":
                src_index = tableau.index(source_col)
                foundation_index = SUITS.index(card.suit)
                start_pos = (card.rect.x, card.rect.y)
                target_pos = (WIDTH - (4 - foundation_index) * SPACING_X, FOUNDATION_Y)
                animate_move(card, start_pos, target_pos, duration=duration_val, 
                draw_func=draw_table, clock=clock,
                extra_draw_args=(screen, tableau, foundations,
                            max(total_time - (pygame.time.get_ticks() - start_time), 0),
                            score, 0, False, None, False))  # hint_active=False, hint_card=None, is_human=False
                source_col.pop()
                foundations[card.suit].append(card)
                score += SCORE_INCREMENT
                moves_count += 1
                recent_moves.append(move)

            elif move_type == "to_tableau":
                src_index = tableau.index(source_col)
                tgt_index = tableau.index(target)
                start_pos = (card.rect.x, card.rect.y)
                target_pos = (SPACING_X * tgt_index + 20, TABLEAU_Y + len(target) * 30)
                
                animate_move(card, start_pos, target_pos, duration=duration_val, 
                draw_func=draw_table, clock=clock,
                extra_draw_args=(screen, tableau, foundations,
                            max(total_time - (pygame.time.get_ticks() - start_time), 0),
                            score, 0, False, None, False))  # hint_active=False, hint_card=None, is_human=False
                source_col.pop()
                target.append(card)
                moves_count += 1
                recent_moves.append(move)

            update_positions(tableau)
            
            if len(recent_moves) >= 6:
                m1, m2, m3, m4, m5, m6 = recent_moves[-6:]
                if m1 == m3 == m5 and m2 == m4 == m6:
                    running = False
                    action = game_over_screen(score, moves_count, elapsed_time,"repeating_moves")
                    if action == "menu":
                        main_menu()
                    elif action == "play_again":
                        ai_options_menu(tableau=initial_tableau)
                    return

            draw_table(screen, tableau, foundations, remaining_time, score, undo_count=0, is_human=False)
            pygame.display.flip()
            if display_mode:
                pygame.time.delay(1000)
            clock.tick(60)

# --- Menus ---
def main_menu():
    menu_running = True
    buttons = {
        "Play": pygame.Rect(WIDTH//2 - 100, 200, 200, 50),
        "Options": pygame.Rect(WIDTH//2 - 100, 270, 200, 50),
        "Help": pygame.Rect(WIDTH//2 - 100, 340, 200, 50),
        "Exit": pygame.Rect(WIDTH//2 - 100, 410, 200, 50)
    }
    while menu_running:
        screen.fill(BACKGROUND_COLOR)
        for text, rect in buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            label = font.render(text, True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == "Play":
                            player_mode_menu()
                        elif text == "Options":
                            options_menu()
                        elif text == "Help":
                            help_menu()
                        elif text == "Exit":
                            pygame.quit()
                            sys.exit()
def options_menu():
    options_running = True
    while options_running:
        screen.fill(BACKGROUND_COLOR)
        # TODO 
        label = font.render("Options (Press any key to return)", True, TEXT_COLOR)
        screen.blit(label, (WIDTH//2 - label.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                options_running = False

def help_menu():
    help_running = True
    while help_running:
        screen.fill(BACKGROUND_COLOR)
        lines = [
            "Help:",
            "Build the four foundation piles up in Suit from Ace to King.",
            "Cards on the tableau are built down regardless of suit.",
            "You can move only one card at a time.",
            "Empty spaces cannot be filled.",
            "Press any key to return."
        ]
        y_offset = 100 
        for line in lines:
            label = small_font.render(line, True, TEXT_COLOR)
            screen.blit(label, (50, y_offset)) 
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                help_running = False

def player_mode_menu(tableau=None):
    mode_running = True
    buttons = {
        "Human": pygame.Rect(WIDTH//2 - 100, 250, 200, 50),
        "AI": pygame.Rect(WIDTH//2 - 100, 320, 200, 50),
        "Return": pygame.Rect(WIDTH//2 - 100, 390, 200, 50)
    }
    while mode_running:
        screen.fill(BACKGROUND_COLOR)
        title = font.render("Select Player Mode", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        for text, rect in buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            label = font.render(text, True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == "Human":
                            human_options_menu(tableau)
                        elif text == "AI":
                            ai_options_menu(tableau)
                        elif text == "Return":
                            main_menu()
                        mode_running = False
                        break

def human_options_menu(tableau=None):
    options_running = True
    difficulty = 13
    duration = 12
    diff_rect_decr = pygame.Rect(WIDTH//2 - 150, 250, 50, 40)
    diff_rect_incr = pygame.Rect(WIDTH//2 + 100, 250, 50, 40)
    duration_rect_decr = pygame.Rect(WIDTH//2 - 150, 310, 50, 40)
    duration_rect_incr = pygame.Rect(WIDTH//2 + 100, 310, 50, 40)
    start_rect = pygame.Rect(WIDTH//2 - 100, 370, 200, 50)
    return_rect = pygame.Rect(WIDTH//2 - 100, 510, 200, 50)
    read_from_file_rect = pygame.Rect(WIDTH//2 - 100, 440, 200, 50)
    while options_running:
        screen.fill(BACKGROUND_COLOR)
        title = font.render("Human Options", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 180))
        if tableau == None:
            diff_text = font.render(f"Cards per Suit: {difficulty}", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, pygame.Rect(WIDTH//2 - 100, 250, 200, 40))
            screen.blit(diff_text, (WIDTH//2 - diff_text.get_width()//2, 255))

            diff_decr_text = font.render("-", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, diff_rect_decr)
            screen.blit(diff_decr_text, (diff_rect_decr.x + 15, diff_rect_decr.y + 5))

            diff_incr_text = font.render("+", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, diff_rect_incr)
            screen.blit(diff_incr_text, (diff_rect_incr.x + 15, diff_rect_incr.y + 5))
        else:
            diff_text = font.render(f"Deck already chosen!", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, pygame.Rect(WIDTH//2 - 100, 250, 200, 40))
            screen.blit(diff_text, (WIDTH//2 - diff_text.get_width()//2, 255))
        
        duration_text = font.render(f"Duration (min): {duration}", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, pygame.Rect(WIDTH//2 - 100, 310, 200, 40))
        screen.blit(duration_text, (WIDTH//2 - duration_text.get_width()//2, 315))

        duration_decr_text = font.render("-", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, duration_rect_decr)
        screen.blit(duration_decr_text, (duration_rect_decr.x + 15, duration_rect_decr.y + 5))

        duration_incr_text = font.render("+", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, duration_rect_incr)
        screen.blit(duration_incr_text, (duration_rect_incr.x + 15, duration_rect_incr.y + 5))

        start_text = font.render("Start Game", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, start_rect)
        screen.blit(start_text, (start_rect.x + 10, start_rect.y + 5))

        return_text = font.render("Return", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, return_rect)
        screen.blit(return_text, (return_rect.x + 10, return_rect.y + 5))

        read_file_text = font.render("Read from File", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, read_from_file_rect)
        screen.blit(read_file_text, (read_from_file_rect.x + 10, read_from_file_rect.y + 5))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if diff_rect_decr.collidepoint(event.pos):
                    if difficulty > 4:
                        difficulty -= 1
                elif diff_rect_incr.collidepoint(event.pos):
                    if difficulty < 13:
                        difficulty += 1
                elif duration_rect_decr.collidepoint(event.pos):
                    if duration > 1:
                        duration -= 1
                elif duration_rect_incr.collidepoint(event.pos):
                    duration += 1
                elif start_rect.collidepoint(event.pos):
                    options_running = False
                    if tableau != None:
                        difficulty = len(tableau)
                        game_loop(difficulty, duration,tableau)
                    else: 
                        game_loop(difficulty, duration,tableau)
                elif return_rect.collidepoint(event.pos):
                    options_running = False
                    main_menu()
                elif read_from_file_rect.collidepoint(event.pos):
                    options_running = False
                    game_loop(difficulty, duration, None, read_from_file=True)

def ai_options_menu(tableau=None):
    '''
    import pygame
    from constants import MAX_USELESS_MOVES, WIDTH, HEIGHT, BACKGROUND_COLOR, BUTTON_COLOR, TEXT_COLOR
    from game import ai_game_loop, main_menu
    '''
    options_running = True
    algorithm_options = ["Simple", "Random", "DFS", "DFS Improved", "Iterative Deepening", "A*", "Weighted A*", "Greedy"]
    algorithm_index = 0
    difficulty = 13
    duration = 12
    max_useless = MAX_USELESS_MOVES 
    depth_limit = DEPTH_LIMIT
    display_mode = True
    weight = 1.5                    # Default for Weighted A*

    # Helper function to draw a numeric control
    def draw_numeric_control(label, value, center_rect, minus_rect, plus_rect):
        control_text = font.render(f"{label}: {value}", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, center_rect)
        screen.blit(control_text, (center_rect.x + (center_rect.width - control_text.get_width()) // 2,
                                   center_rect.y + (center_rect.height - control_text.get_height()) // 2))
        minus_text = font.render("-", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, minus_rect)
        screen.blit(minus_text, (minus_rect.x + (minus_rect.width - minus_text.get_width()) // 2,
                                 minus_rect.y + (minus_rect.height - minus_text.get_height()) // 2))
        plus_text = font.render("+", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, plus_rect)
        screen.blit(plus_text, (plus_rect.x + (plus_rect.width - plus_text.get_width()) // 2,
                                plus_rect.y + (plus_rect.height - plus_text.get_height()) // 2))

    # Helper function to update a value when a plus or minus button is clicked.
    # It uses a small step (step_small) when the value is low and a larger step (step_large) otherwise.
    def update_value_on_click(pos, minus_rect, plus_rect, value, min_val, max_val, step_small, step_large):
        if minus_rect.collidepoint(pos):
            value -= step_large if value > step_large else step_small
            if value < min_val:
                value = min_val
        elif plus_rect.collidepoint(pos):
            value += step_large if value < max_val - step_large else step_small
            if value > max_val:
                value = max_val
        return value

    # Define control rectangles (using a consistent layout)
    algo_rect   = pygame.Rect(WIDTH//2 - 150, 200, 300, 40)
    
    # Difficulty (if deck not already chosen)
    diff_center = pygame.Rect(WIDTH//2 - 100, 260, 200, 40)
    diff_minus  = pygame.Rect(WIDTH//2 - 150, 260, 50, 40)
    diff_plus   = pygame.Rect(WIDTH//2 + 100, 260, 50, 40)
    
    # Duration control
    dur_center  = pygame.Rect(WIDTH//2 - 100, 320, 200, 40)
    dur_minus   = pygame.Rect(WIDTH//2 - 150, 320, 50, 40)
    dur_plus    = pygame.Rect(WIDTH//2 + 100, 320, 50, 40)
    
    # For DFS and Iterative Deepening: max_useless control
    mu_center   = pygame.Rect(WIDTH//2 - 100, 380, 200, 40)
    mu_minus    = pygame.Rect(WIDTH//2 - 150, 380, 50, 40)
    mu_plus     = pygame.Rect(WIDTH//2 + 100, 380, 50, 40)
    
    # New: Depth limit control for DFS/Iterative Deepening
    dl_center   = pygame.Rect(WIDTH//2 - 100, 440, 200, 40)
    dl_minus    = pygame.Rect(WIDTH//2 - 150, 440, 50, 40)
    dl_plus     = pygame.Rect(WIDTH//2 + 100, 440, 50, 40)
    
    # Display mode toggle
    display_rect = pygame.Rect(WIDTH//2 - 150, 500, 300, 40)
    
    # For Weighted A*: weight control
    weight_center = pygame.Rect(WIDTH//2 - 100, 560, 200, 40)
    weight_minus  = pygame.Rect(WIDTH//2 - 150, 560, 50, 40)
    weight_plus   = pygame.Rect(WIDTH//2 + 100, 560, 50, 40)
    
    # Start and Return buttons
    start_rect  = pygame.Rect(WIDTH//2 - 100, 620, 200, 50)
    return_rect = pygame.Rect(WIDTH//2 - 100, 760, 200, 50)
    read_from_file_rect = pygame.Rect(WIDTH//2 - 100, 690, 200, 50)
    
    while options_running:
        screen.fill(BACKGROUND_COLOR)
        title = font.render("AI Options", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
        
        # Algorithm selection (clicking this rectangle cycles through algorithms)
        algo_text = font.render(f"Algorithm: {algorithm_options[algorithm_index]}", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, algo_rect)
        screen.blit(algo_text, (algo_rect.x + 10, algo_rect.y + 5))
        
        # Difficulty selection (only if no deck has been chosen yet)
        if tableau is None:
            draw_numeric_control("Cards per Suit", difficulty, diff_center, diff_minus, diff_plus)
            
            read_file_text = font.render("Read from File", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, read_from_file_rect)
            screen.blit(read_file_text, (read_from_file_rect.x + 10, read_from_file_rect.y + 5))
        else:
            diff_text = font.render("Deck already chosen!", True, TEXT_COLOR)
            pygame.draw.rect(screen, BUTTON_COLOR, diff_center)
            screen.blit(diff_text, (diff_center.x + (diff_center.width - diff_text.get_width()) // 2,
                                    diff_center.y + (diff_center.height - diff_text.get_height()) // 2))
        
        # Duration selection
        draw_numeric_control("Duration (min)", duration, dur_center, dur_minus, dur_plus)
        
        # For DFS and Iterative Deepening, show max_useless and depth_limit controls
        if algorithm_options[algorithm_index] in ["DFS", "DFS Improved","Iterative Deepening"]:
            draw_numeric_control("Useless Moves", max_useless, mu_center, mu_minus, mu_plus)
            draw_numeric_control("Depth Limit", depth_limit, dl_center, dl_minus, dl_plus)
        
        # Display mode toggle button
        display_str = "Slow Mode (1 sec delay)" if display_mode else "Fast Mode (no delay)"
        disp_text = font.render(f"Display Mode: {display_str}", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, display_rect)
        screen.blit(disp_text, (display_rect.x + (display_rect.width - disp_text.get_width()) // 2,
                                display_rect.y + (display_rect.height - disp_text.get_height()) // 2))
        
        # For Weighted A*, show weight control
        if algorithm_options[algorithm_index] == "Weighted A*":
            draw_numeric_control("Heuristic Weight", f"{weight:.1f}", weight_center, weight_minus, weight_plus)
        
        # Start and Return buttons
        start_text = font.render("Start Game", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, start_rect)
        screen.blit(start_text, (start_rect.x + (start_rect.width - start_text.get_width()) // 2,
                                 start_rect.y + (start_rect.height - start_text.get_height()) // 2))
        ret_text = font.render("Return", True, TEXT_COLOR)
        pygame.draw.rect(screen, BUTTON_COLOR, return_rect)
        screen.blit(ret_text, (return_rect.x + (return_rect.width - ret_text.get_width()) // 2,
                               return_rect.y + (return_rect.height - ret_text.get_height()) // 2))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if algo_rect.collidepoint(pos):
                    algorithm_index = (algorithm_index + 1) % len(algorithm_options)
                elif diff_minus.collidepoint(pos) and tableau is None:
                    difficulty = update_value_on_click(pos, diff_minus, diff_plus, difficulty, 4, 13, 1, 1)
                elif diff_plus.collidepoint(pos) and tableau is None:
                    difficulty = update_value_on_click(pos, diff_minus, diff_plus, difficulty, 4, 13, 1, 1)
                elif dur_minus.collidepoint(pos):
                    duration = update_value_on_click(pos, dur_minus, dur_plus, duration, 1, 120, 1, 5)
                elif dur_plus.collidepoint(pos):
                    duration = update_value_on_click(pos, dur_minus, dur_plus, duration, 1, 120, 1, 5)
                elif algorithm_options[algorithm_index] in ["DFS", "DFS Improved", "Iterative Deepening"]:
                    if mu_minus.collidepoint(pos):
                        max_useless = update_value_on_click(pos, mu_minus, mu_plus, max_useless, 1, MAX_USELESS_MOVES, 1, 10)
                    elif mu_plus.collidepoint(pos):
                        max_useless = update_value_on_click(pos, mu_minus, mu_plus, max_useless, 1, MAX_USELESS_MOVES, 1, 10)
                    elif dl_minus.collidepoint(pos):
                        depth_limit = update_value_on_click(pos, dl_minus, dl_plus, depth_limit, 1, 1000, 1, 10)
                    elif dl_plus.collidepoint(pos):
                        depth_limit = update_value_on_click(pos, dl_minus, dl_plus, depth_limit, 1, 1000, 1, 10)
                if display_rect.collidepoint(pos):
                    display_mode = not display_mode
                if algorithm_options[algorithm_index] == "Weighted A*":
                    if weight_minus.collidepoint(pos):
                        weight = max(1.0, round(weight - 0.1, 1))
                    elif weight_plus.collidepoint(pos):
                        weight = min(5.0, round(weight + 0.1, 1))
                if start_rect.collidepoint(pos):
                    options_running = False
                    ai_game_loop(
                        algorithm=algorithm_options[algorithm_index],
                        difficulty=(len(tableau) if tableau is not None else difficulty),
                        game_duration=duration,
                        display_mode=display_mode,
                        max_useless=max_useless,
                        depth_limit=depth_limit,  # new parameter passed here
                        weight=weight,
                        tableau=tableau
                    )
                elif return_rect.collidepoint(pos):
                    options_running = False
                    main_menu()
                elif read_from_file_rect.collidepoint(event.pos):
                    options_running = False
                    ai_game_loop(
                        algorithm=algorithm_options[algorithm_index],
                        difficulty=(len(tableau) if tableau is not None else difficulty),
                        game_duration=duration,
                        display_mode=display_mode,
                        max_useless=max_useless,
                        depth_limit=depth_limit,  # new parameter passed here
                        weight=weight,
                        tableau=tableau,
                        read_from_file=True
                    )
