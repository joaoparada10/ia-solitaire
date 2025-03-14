import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1600, 800
CARD_WIDTH, CARD_HEIGHT = 80, 120 # (0,0) é o canto inferior esquerdo da carta
SPACING_X, SPACING_Y = 100, 30
FOUNDATION_Y = 20
TABLEAU_Y = 180
BACKGROUND_COLOR = (34, 139, 34)  # Green table
CARD_COLOR = (255,255,255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 149, 237)
TEXT_COLOR = (255, 255, 255)
DOUBLE_CLICK_THRESHOLD = 400  # milliseconds
SCORE_INCREMENT = 50
DIFFICULTY = 13 # Hardest 

# Screen and fonts
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Baker's Dozen Solitaire")
font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)

# Load card images
CARD_IMAGES = {}
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king']
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}

# TODO Meter isto em função

for suit in SUITS:
    for rank in RANKS:
        filename = f"png/{rank}_of_{suit}.png"
        CARD_IMAGES[(rank, suit)] = pygame.transform.scale(
            pygame.image.load(filename), (CARD_WIDTH, CARD_HEIGHT)
        )

# TODO Fazer Class Board

# Card Class
class Card:
    def __init__(self, rank, suit, x, y):
        self.rank = rank
        self.suit = suit
        self.image = CARD_IMAGES[(rank, suit)]
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.selected = False
        self.offset_x = 0
        self.offset_y = 0

    def draw(self, screen):
        pygame.draw.rect(screen, CARD_COLOR, self.rect)
        screen.blit(self.image, (self.rect.x, self.rect.y))

def create_deck():
    deck = [Card(rank, suit, 0, 0) for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck

def deal_cards(deck):
    tableau = [[] for _ in range(13)]
    
    # Separate Kings from the rest of the deck
    kings = [card for card in deck if card.rank == 'king']
    non_kings = [card for card in deck if card.rank != 'king']

    # Shuffle non-King cards
    random.shuffle(non_kings)

    # Randomly select 4 piles to place Kings at the bottom
    king_piles = random.sample(range(13), 4)  # Randomly choose 4 piles out of 13

    # Add one King to the bottom of the randomly selected piles
    for pile in king_piles:
        tableau[pile].insert(0, kings.pop())  # Insert King at the bottom (index 0)

    # Deal non-King cards into all 13 columns
    # Each pile should have 4 cards in total (1 King + 3 non-Kings or 4 non-Kings)
    for i in range(13):
        # If this pile has a King, add 3 more non-King cards
        if i in king_piles:
            for _ in range(3):
                card = non_kings.pop()
                tableau[i].append(card)
        # If this pile does not have a King, add 4 non-King cards
        else:
            for _ in range(4):
                card = non_kings.pop()
                tableau[i].append(card)

    # Set positions for cards: each column's cards get a vertical offset based on their index
    for col_index, col in enumerate(tableau):
        for card_index, card in enumerate(col):
            card.rect.x = SPACING_X * col_index + 20
            card.rect.y = TABLEAU_Y + card_index * 30
    return tableau

def draw_table(screen, tableau, foundations, remaining_time, score, undo_count):
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

    # Format the remaining time as MM:SS
    time_text = font.render(f"Time: {format_time(remaining_time)}", True, TEXT_COLOR)
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(time_text, (20, 20))
    screen.blit(score_text, (20, 50))

    return_to_menu_button_rect = pygame.Rect(20, HEIGHT - 50, 170, 40)  # (x, y, width, height)
    pygame.draw.rect(screen, BUTTON_COLOR, return_to_menu_button_rect)
    return_to_menu_text = font.render("Return to Menu", True, TEXT_COLOR)
    screen.blit(return_to_menu_text, (25, HEIGHT - 45))  # Adjust text position for alignment

    # Draw the undo button
    undo_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, 100, 30)
    pygame.draw.rect(screen, BUTTON_COLOR, undo_button_rect)
    undo_text = font.render(f"Undo ({undo_count})", True, TEXT_COLOR)
    screen.blit(undo_text, (WIDTH - 140, HEIGHT - 45))
    
    pygame.display.flip()

def is_valid_move(card, target_col):
    if not target_col:
        return False  # Any card can not be placed in an empty column
    top_card = target_col[-1]
    return RANK_VALUES[card.rank] == RANK_VALUES[top_card.rank] - 1  # Must be one rank lower

def is_valid_foundation_move(card, foundation_pile):
    if not foundation_pile:
        return card.rank == 'ace'  # Foundation must start with an Ace
    top_card = foundation_pile[-1]
    return card.suit == top_card.suit and RANK_VALUES[card.rank] == RANK_VALUES[top_card.rank] + 1  # Must be next in sequence

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
                            game_loop()
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

        # Define the help text lines
        lines = [
            "Help:",
            "Build the four foundation piles up in Suit from Ace to King.",
            "Cards on the tableau are built down regardless of suit.",
            "You can move only one card at a time.",
            "Empty spaces cannot be filled.",
            "Press any key to return."
        ]

        # Render each line separately and position them vertically
        y_offset = 100  # Starting Y position for the first line
        for line in lines:
            label = small_font.render(line, True, TEXT_COLOR)
            screen.blit(label, (50, y_offset))  # Position the line at (50, y_offset)
            y_offset += 30  # Move down by 30 pixels for the next line

        pygame.display.flip()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                help_running = False


def find_card_column(card, tableau):
    for col in tableau:
        if col and col[-1] == card:
            return col
    return None

# TODO retirar coisas do Game Loop e passar a funções separadas
def format_time(milliseconds):
    """Convert milliseconds to a string in the format MM:SS."""
    seconds = milliseconds // 1000  # Convert milliseconds to seconds
    minutes = seconds // 60  # Extract minutes
    seconds = seconds % 60  # Extract remaining seconds
    return f"{minutes:02}:{seconds:02}"  # Format as MM:SS

def has_valid_moves(tableau, foundations):
    """
    Check if there are any valid moves left in the game.
    Returns True if there are valid moves, False otherwise.
    """
    # Check if any card in the tableau can be moved to another tableau pile
    for source_col in tableau:
        if not source_col:
            continue  # Skip empty columns
        source_card = source_col[-1]  # Get the top card of the column
        for target_col in tableau:
            if source_col == target_col:
                continue  # Skip the same column
            if not target_col:
                continue  # Cannot move to an empty column in Baker's Dozen
            target_card = target_col[-1]
            if is_valid_move(source_card, target_col):
                return True  # Valid move found

    # Check if any card in the tableau can be moved to a foundation pile
    for col in tableau:
        if not col:
            continue  # Skip empty columns
        card = col[-1]  # Get the top card of the column
        for suit, foundation_pile in foundations.items():
            if is_valid_foundation_move(card, foundation_pile):
                return True  # Valid move found

    # No valid moves found
    return False

def check_win(tableau):
    """Check if all cards have been moved to the foundation, leaving the tableau empty."""
    for col in tableau:
        if col:  # If any column in the tableau is not empty
            return False
    return True  # All columns are empty

def game_over_screen(score, reason="time_up"):
    """Display the game over screen with 'Return to Menu' and 'Play Again' buttons."""
    game_over_running = True
    buttons = {
        "Return to Menu": pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50),
        "Play Again": pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)
    }

    while game_over_running:
        screen.fill(BACKGROUND_COLOR)

        # Display game over text based on the reason
        if reason == "time_up":
            game_over_text = font.render("Time's up! Game over.", True, TEXT_COLOR)
        elif reason == "no_valid_moves":
            game_over_text = font.render("No valid moves left! Game over.", True, TEXT_COLOR)
        else:
            game_over_text = font.render("Game over.", True, TEXT_COLOR)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))

        # Display total score
        score_text = font.render(f"Total Score: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 50))

        # Draw buttons
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
                        if text == "Return to Menu":
                            return "menu"
                        elif text == "Play Again":
                            return "play_again"

def winning_screen(score):
    """Display the winning screen with 'Return to Menu' and 'Play Again' buttons."""
    win_running = True
    buttons = {
        "Return to Menu": pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50),
        "Play Again": pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)
    }

    while win_running:
        screen.fill(BACKGROUND_COLOR)

        # Display winning text
        win_text = font.render("Congratulations! You won!", True, TEXT_COLOR)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 100))

        # Display total score
        score_text = font.render(f"Total Score: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 50))

        # Draw buttons
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
                        if text == "Return to Menu":
                            return "menu"
                        elif text == "Play Again":
                            return "play_again"

def game_loop():
    deck = create_deck()
    tableau = deal_cards(deck)
    foundations = {suit: [] for suit in SUITS}
    running = True
    selected_card = None
    original_position = None
    source_col = None

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    total_time = 12 * 60 * 1000  # 12 minutes in milliseconds
    elapsed_time = 0

    score = 0

    # Undo variables
    undo_stack = []  # Stores previous game states and card positions for valid moves
    undo_count = 3  # Number of undos remaining

    # Variables for double-click detection
    last_click_time = 0
    last_clicked_card = None

    # Define the "Return to Menu" button (bottom-left corner)

    while running:
        # Calculate remaining time
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_time = max(total_time - elapsed_time, 0)  # Ensure time doesn't go below 0

        # Check if time has run out
        if remaining_time <= 0:
            running = False
            print("Time's up! Game over.")
            action = game_over_screen(score, reason="time_up")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                game_loop()
            return

        # Check if the player has won
        if check_win(tableau):
            running = False
            print("Congratulations! You won!")
            action = winning_screen(score)
            if action == "menu":
                main_menu()
            elif action == "play_again":
                game_loop()
            return

        # Check if there are no valid moves left 
        if not has_valid_moves(tableau, foundations):
            running = False
            print("No valid moves left! You are stuck.")
            action = game_over_screen(score, reason="no_valid_moves")
            if action == "menu":
                main_menu()
            elif action == "play_again":
                game_loop()
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the "Return to Menu" button is clicked
                return_to_menu_button = pygame.Rect(20, HEIGHT - 50, 170, 40)
                if return_to_menu_button.collidepoint(event.pos):
                    running = False
                    main_menu()
                    return  # Exit the game loop and return to the main menu

                # Check if the undo button is clicked
                undo_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 50, 100, 30)
                if undo_button_rect.collidepoint(event.pos) and undo_count > 0:
                    if undo_stack:
                        # Revert to the previous game state and card positions
                        tableau, foundations, score, card_positions = undo_stack.pop()
                        for col in tableau:
                            for card in col:
                                card.rect.x, card.rect.y = card_positions[id(card)]
                        for suit, foundation_pile in foundations.items():
                            if foundation_pile:
                                foundation_pile[-1].rect.x = WIDTH - (4 - list(foundations.keys()).index(suit)) * SPACING_X
                                foundation_pile[-1].rect.y = FOUNDATION_Y
                        undo_count -= 1

                current_time = pygame.time.get_ticks()

                # Check for double-click on a card
                for col in tableau:
                    if col:
                        card = col[-1]
                        if card.rect.collidepoint(event.pos):
                            if last_clicked_card == card and (current_time - last_click_time) < DOUBLE_CLICK_THRESHOLD:
                                # Double-click detected: attempt to move card to foundation.
                                source_col = find_card_column(card, tableau)
                                if source_col is not None:
                                    # Save the current game state and card positions before making the move
                                    card_positions = {id(card): (card.rect.x, card.rect.y) for col in tableau for card in col}
                                    undo_stack.append(([col.copy() for col in tableau], {suit: pile.copy() for suit, pile in foundations.items()}, score, card_positions))
                                    for suit, foundation_pile in foundations.items():
                                        if suit == card.suit and is_valid_foundation_move(card, foundation_pile):
                                            source_col.remove(card)
                                            foundation_pile.append(card)
                                            score += SCORE_INCREMENT
                                            break
                                last_click_time = 0
                                last_clicked_card = None
                                break
                            else:
                                selected_card = card
                                original_position = (card.rect.x, card.rect.y)
                                card.offset_x = event.pos[0] - card.rect.x
                                card.offset_y = event.pos[1] - card.rect.y
                                # Save the current game state and card positions before making the move
                                card_positions = {id(card): (card.rect.x, card.rect.y) for col in tableau for card in col}
                                undo_stack.append(([col.copy() for col in tableau], {suit: pile.copy() for suit, pile in foundations.items()}, score, card_positions))
                                # Set last_clicked_card for future double-click detection.
                                last_clicked_card = card
                                last_click_time = current_time
                                break

            elif event.type == pygame.MOUSEMOTION:
                if selected_card:
                    selected_card.rect.x = event.pos[0] - selected_card.offset_x
                    selected_card.rect.y = event.pos[1] - selected_card.offset_y

            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_card:
                    source_col = find_card_column(selected_card, tableau)
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

                    # Check if moving to a foundation
                    moved_to_foundation = False
                    for suit, foundation_pile in foundations.items():
                        if foundation_pile:
                            if foundation_pile[-1].rect.collidepoint(event.pos) and is_valid_foundation_move(selected_card, foundation_pile):
                                source_col.remove(selected_card)
                                foundation_pile.append(selected_card)
                                score += SCORE_INCREMENT
                                moved_to_foundation = True
                                break
                        else:
                            foundation_x = WIDTH - (4 - list(foundations.keys()).index(suit)) * SPACING_X
                            foundation_rect = pygame.Rect(foundation_x, FOUNDATION_Y, CARD_WIDTH, CARD_HEIGHT)
                            if foundation_rect.collidepoint(event.pos) and selected_card.rank == 'ace':
                                source_col.remove(selected_card)
                                foundation_pile.append(selected_card)
                                score += SCORE_INCREMENT
                                moved_to_foundation = True
                                break

                    # Normal tableau move
                    if selected_card and not moved_to_foundation:
                        if target_col and is_valid_move(selected_card, target_col):
                            source_col.remove(selected_card)
                            target_col.append(selected_card)
                        else:
                            selected_card.rect.x, selected_card.rect.y = original_position  # Reset position if move is invalid
                            # Remove the last state from the undo stack if the move was invalid
                            if undo_stack:
                                undo_stack.pop()
                    selected_card = None
                    original_position = None
                    source_col = None

        # Draw the table, foundations, elapsed time, and score
        draw_table(screen, tableau, foundations, remaining_time, score, undo_count)

        # Draw the "Return to Menu" button (bottom-left corner)
        

        pygame.display.flip()
        clock.tick(60)

main_menu()

