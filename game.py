import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 600
CARD_WIDTH, CARD_HEIGHT = 80, 120 # (0,0) é o canto inferior esquerdo da carta
SPACING_X, SPACING_Y = 100, 30
FOUNDATION_Y = 20
TABLEAU_Y = 180
BACKGROUND_COLOR = (34, 139, 34)  # Green table
CARD_COLOR = (255,255,255)

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

# Game Initialization
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Baker's Dozen Solitaire")


# TODO Garantir que Kings ficam sempre em baixo das outras todas

def create_deck():
    deck = [Card(rank, suit, 0, 0) for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck

def deal_cards(deck):
    tableau = [[] for _ in range(13)]
    index = 0
    for col in tableau:
        for _ in range(4):
            card = deck.pop()
            col.append(card)
            card.rect.x = SPACING_X * index + 20
            card.rect.y = TABLEAU_Y + len(col) * 30
        index += 1
    return tableau

def draw_table(screen, tableau, foundations):
    screen.fill(BACKGROUND_COLOR)
    for col in tableau:
        for card in col:
            card.draw(screen)
    for foundation in foundations:
        if foundations[foundation]:
            foundations[foundation][-1].draw(screen)
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


# TODO retirar coisas do Game Loop e passar a funções separadas

# Main Game Loop
deck = create_deck()
tableau = deal_cards(deck)
foundations = {suit: [] for suit in SUITS}  # Each suit has its own foundation pile
running = True
selected_card = None
original_position = None
source_col = None

while running:
    screen.fill(BACKGROUND_COLOR)
    draw_table(screen, tableau, foundations)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for col in tableau:
                if col:
                    card = col[-1]  # Only top card is movable
                    if card.rect.collidepoint(event.pos):
                        selected_card = card
                        original_position = (card.rect.x, card.rect.y)
                        card.offset_x = event.pos[0] - card.rect.x
                        card.offset_y = event.pos[1] - card.rect.y
                        source_col = col
                        break
        elif event.type == pygame.MOUSEMOTION:
            if selected_card:
                selected_card.rect.x = event.pos[0] - selected_card.offset_x
                selected_card.rect.y = event.pos[1] - selected_card.offset_y
        elif event.type == pygame.MOUSEBUTTONUP:
            if selected_card:
                target_col = None
                for col in tableau:
                    if col and col[-1].rect.collidepoint(event.pos):
                        target_col = col
                        break
                    elif not col and (SPACING_X * tableau.index(col) + 20 < event.pos[0] < SPACING_X * (tableau.index(col) + 1)):
                        target_col = col
                        break
                
                # Check if moving to a foundation
                for suit, foundation_pile in foundations.items():
                    if foundation_pile:
                        if foundation_pile[-1].rect.collidepoint(event.pos) and is_valid_foundation_move(selected_card, foundation_pile):
                            source_col.remove(selected_card)
                            foundation_pile.append(selected_card)
                            selected_card = None
                            original_position = None
                            source_col = None
                            break
                    else:
                        foundation_x = WIDTH - (4 - list(foundations.keys()).index(suit)) * SPACING_X
                        foundation_rect = pygame.Rect(foundation_x, FOUNDATION_Y, CARD_WIDTH, CARD_HEIGHT)
                        if foundation_rect.collidepoint(event.pos) and selected_card.rank == 'ace':
                            source_col.remove(selected_card)
                            foundation_pile.append(selected_card)
                            selected_card = None
                            original_position = None
                            source_col = None
                            break
                
                # Normal tableau move
                if selected_card:
                    if target_col and is_valid_move(selected_card, target_col):
                        source_col.remove(selected_card)
                        target_col.append(selected_card)
                    else:
                        selected_card.rect.x, selected_card.rect.y = original_position  # Reset position if move is invalid
                    selected_card = None
                    original_position = None
                    source_col = None
    
    pygame.display.update()

pygame.quit()
