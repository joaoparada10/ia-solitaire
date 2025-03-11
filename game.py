import pygame
import random

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
    # Deal cards into 13 columns, 4 cards each.
    for i in range(13):
        for _ in range(4):
            card = deck.pop()
            if card.rank == 'king':
                tableau[i].insert(0, card)  # Insert kings at the top of the column.
            else:
                tableau[i].append(card)
    # Set positions for cards: each column's cards get a vertical offset based on their index.
    for col_index, col in enumerate(tableau):
        for card_index, card in enumerate(col):
            card.rect.x = SPACING_X * col_index + 20
            card.rect.y = TABLEAU_Y + card_index * 30
    return tableau

def draw_table(screen, tableau, foundations,elapsed_time,score):
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

    time_text = font.render(f"Time: {int(elapsed_time/1000)} sec", True, TEXT_COLOR)
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(time_text, (20, 20))
    screen.blit(score_text, (20, 50))

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
        lines = [
            "Help:",
            "Build the four foundation piles up in Suit from Ace to King."
            "Cards on the tableau are build down regardless of suit."
            "You can move only one card at a time."
            "Empty spaces cannot be filled."
            "Press any key to return."
        ]
        for i, line in enumerate(lines):
            label = small_font.render(line, True, TEXT_COLOR)
            screen.blit(label, (50, 100 + i * 30))
        pygame.display.flip()
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
def game_loop():
    deck = create_deck()
    tableau = deal_cards(deck)
    foundations = {suit: [] for suit in SUITS}  # Each suit has its own foundation pile
    running = True
    selected_card = None
    original_position = None
    source_col = None

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    score = 0

    # Variables for double-click detection
    last_click_time = 0
    last_clicked_card = None

    while running:
        elapsed_time = pygame.time.get_ticks() - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
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
                    selected_card = None
                    original_position = None
                    source_col = None
        
        draw_table(screen, tableau, foundations, elapsed_time, score)
        clock.tick(60)

main_menu()
