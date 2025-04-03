import pygame
import constants
import sys

def load_card_images():
    CARD_IMAGES = {}
    for suit in constants.SUITS:
        for rank in constants.RANKS:
            filename = f"png/{rank}_of_{suit}.png"
            image = pygame.image.load(filename)
            image = pygame.transform.scale(image, (constants.CARD_WIDTH, constants.CARD_HEIGHT))
            CARD_IMAGES[(rank, suit)] = image
    return CARD_IMAGES

def is_valid_move(card, target_col):
    if not target_col:
        return False
    top_card = target_col[-1]
    return constants.RANK_VALUES[card.rank] == constants.RANK_VALUES[top_card.rank] - 1

def is_valid_foundation_move(card, foundation_pile):
    if not foundation_pile:
        return card.rank == 'ace'
    top_card = foundation_pile[-1]
    return card.suit == top_card.suit and constants.RANK_VALUES[card.rank] == constants.RANK_VALUES[top_card.rank] + 1

def format_time(milliseconds):
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

def has_valid_moves(tableau, foundations):
    for source_col in tableau:
        if not source_col:
            continue
        source_card = source_col[-1]
        for target_col in tableau:
            if source_col == target_col:
                continue
            if not target_col:
                continue
            if is_valid_move(source_card, target_col):
                return True
    for col in tableau:
        if not col:
            continue
        card = col[-1]
        for suit, foundation_pile in foundations.items():
            if is_valid_foundation_move(card, foundation_pile):
                return True
    return False

def check_win(tableau):
    return all(len(col) == 0 for col in tableau)

def update_positions(tableau):
    for col_index, col in enumerate(tableau):
        for card_index, card in enumerate(col):
            card.rect.x = constants.SPACING_X * col_index + 20
            card.rect.y = constants.TABLEAU_Y + card_index * 30

def animate_move(card, start_pos, end_pos, duration, draw_func, clock, extra_draw_args):
    """
    Animate card from start_pos to end_pos over the given duration (in milliseconds).
    draw_func is a function (e.g., draw_table) that draws the board.
    extra_draw_args is a tuple of extra parameters to pass to draw_func.
    """
    start_time = pygame.time.get_ticks()
    while True:
        now = pygame.time.get_ticks()
        t = min((now - start_time) / duration, 1)  # 0 <= t <= 1
        # Linear interpolation
        new_x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
        new_y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
        card.rect.x = new_x
        card.rect.y = new_y
        
        # Call draw function with extra parameters (e.g., tableau, foundations, remaining_time, score, etc.)
        draw_func(*extra_draw_args)
        pygame.display.flip()
        clock.tick(60)
        # Process events to keep window responsive.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        if t >= 1:
            break

def get_hint(tableau, foundations):
    """Returns a suggested move for the current game state"""
    # First priority: Move cards to foundation if possible
    for col in tableau:
        if col:
            card = col[-1]
            foundation_pile = foundations[card.suit]
            if is_valid_foundation_move(card, foundation_pile):
                return ("to_foundation", card, col, foundation_pile)
    
    # Second priority: Uncover hidden cards by moving tableau cards
    for src_col in tableau:
        if len(src_col) > 1:  # Only consider moves that uncover cards
            card = src_col[-1]
            for dst_col in tableau:
                if src_col != dst_col and is_valid_move(card, dst_col):
                    return ("to_tableau", card, src_col, dst_col)
    
    # Third priority: Any valid tableau move
    for src_col in tableau:
        if src_col:
            card = src_col[-1]
            for dst_col in tableau:
                if src_col != dst_col and is_valid_move(card, dst_col):
                    return ("to_tableau", card, src_col, dst_col)
    
    return None  # No valid moves found
