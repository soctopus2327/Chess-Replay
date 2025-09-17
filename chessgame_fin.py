import chess.pgn
import pygame
import sys
import time

pygame.init()

HEIGHT = 700  
BOARD_SIZE = 600
MOVES_PER_COLUMN = 20  
COLUMN_WIDTH = 100     

WHITE = (255, 255, 255)
BLACK = (250, 221, 117)
BUTTON_COLOR = (150, 150, 150)
BUTTON_HOVER_COLOR = (250, 221, 117)
TEXT_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (250, 150, 80)  

piece_images = {}
pieces = ['wp', 'wn', 'wb', 'wr', 'wq', 'wk', 'bp', 'bn', 'bb', 'br', 'bq', 'bk']
for piece in pieces:
    piece_images[piece] = pygame.image.load(f'pieces/{piece}.png')

button_icons = {
    "Start": pygame.image.load('buttons/start.jpg'),
    "Back": pygame.image.load('buttons/back.jpg'),
    "Play": pygame.image.load('buttons/play.jpg'),
    "Next": pygame.image.load('buttons/next.jpg'),
    "End": pygame.image.load('buttons/end.jpg')
}

icon_size = (50, 50) 
for key in button_icons:
    button_icons[key] = pygame.transform.scale(button_icons[key], icon_size)

def load_pgn(file_path):
    with open(file_path) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        moves = list(game.mainline_moves())
        white_player = game.headers.get("White", "White") 
        black_player = game.headers.get("Black", "Black")  
        result = game.headers.get("Result", "")
    return moves, white_player, black_player, result

def draw_board(board, screen, last_move=None):
    square = BOARD_SIZE // 8
    font = pygame.font.SysFont(None, 24)

    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK

            # if last_move and (chess.square(col, 7 - row) in [last_move.from_square, last_move.to_square]):
            #     color = HIGHLIGHT_COLOR

            pygame.draw.rect(screen, color, pygame.Rect(col * square, row * square, square, square))

            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                piece_symbol = piece.symbol()
                piece_image = piece_images.get(f"{'w' if piece_symbol.isupper() else 'b'}{piece_symbol.lower()}")
                piece_image = pygame.transform.scale(piece_image, (square, square))
                screen.blit(piece_image, (col * square, row * square))

    for i in range(8):
        row_label = font.render(str(8 - i), True, TEXT_COLOR)
        screen.blit(row_label, (610, i * square + square // 2))

        col_label = font.render(chr(i + ord('a')), True, TEXT_COLOR)
        screen.blit(col_label, (i * square + square // 2, 610))

def draw_buttons(autoplay, screen):
    button_positions = {
        "Start": (20, 640),  
        "Back": (140, 640),  
        "Play": (260, 640),  
        "Next": (380, 640),  
        "End": (500, 640)    
    }

    for name, (x, y) in button_positions.items():
        icon = button_icons[name]
        screen.blit(icon, (x, y))

def handle_buttons(mouse_pos, board, moves, move_index, autoplay, last_move):
    button_width = 100
    button_height = 50
    button_y = 640  
    button_positions = {
        "Start": (20, button_y),
        "Back": (140, button_y),
        "PlayPause": (260, button_y),
        "Next": (380, button_y),
        "End": (500, button_y)
    }

    if pygame.mouse.get_pressed()[0]:
        for name, (x, y) in button_positions.items():
            if x <= mouse_pos[0] <= x + button_width and y <= mouse_pos[1] <= y + button_height:
                if name == "Start":
                    board.reset()
                    move_index = 0
                    autoplay = False
                    last_move = None  
                elif name == "Back" and move_index > 0:
                    move_index -= 1
                    last_move = board.pop()
                    autoplay = False
                elif name == "PlayPause":
                    autoplay = not autoplay 
                elif name == "Next" and move_index < len(moves):
                    last_move = moves[move_index]
                    board.push(moves[move_index])
                    move_index += 1
                    autoplay = False
                elif name == "End":
                    board.reset()
                    for i in range(len(moves)):
                        board.push(moves[i])
                    move_index = len(moves)
                    autoplay = False
    return move_index, autoplay, last_move

def draw_move_list(moves, move_index, white_player, black_player, screen):
    list_start_x = 650  
    list_start_y = 50   
    move_height = 30    
    moves_per_column = MOVES_PER_COLUMN
    column_gap = COLUMN_WIDTH

    font = pygame.font.SysFont(None, 24)  

    board = chess.Board()

    total_moves = len(moves)
    num_columns = (total_moves + moves_per_column - 1) // moves_per_column  

    players_text = f"{black_player} Vs. {white_player}"
    players_surface = pygame.font.SysFont(None, 36).render(players_text, True, TEXT_COLOR)
    screen.blit(players_surface, (list_start_x, list_start_y - 40))  

    for column in range(num_columns):
        start_move = column * moves_per_column
        end_move = min(start_move + moves_per_column, total_moves)

        for i in range(start_move, end_move):
            y_position = list_start_y + (i - start_move) * move_height
            x_position = list_start_x + column * column_gap

            if i == move_index:
                pygame.draw.rect(screen, BUTTON_HOVER_COLOR, (x_position - 10, y_position - 10, 90, move_height))

            move_text = font.render(f"{(i // 2) + 1}. {board.san(moves[i])}", True, TEXT_COLOR)
            screen.blit(move_text, (x_position, y_position))

            if board.is_legal(moves[i]):
                board.push(moves[i])

def simulate_game(pgn_file):
    moves, white_player, black_player, result = load_pgn(pgn_file)
    move_index = 0
    board = chess.Board()
    autoplay = False
    last_button_press_time = 0  
    button_cooldown = 200  
    last_move = None

    total_moves = len(moves)
    num_columns = (total_moves + MOVES_PER_COLUMN - 1) // MOVES_PER_COLUMN  
    dynamic_width = 650 + num_columns * COLUMN_WIDTH  

    # font = pygame.font.SysFont(None, 36)
    # player_text = f"{black_player} Vs. {white_player}"
    # player_text_surface = font.render(player_text, True, TEXT_COLOR)
    # player_text_width = player_text_surface.get_width() + 20

    # minimum_width = max(dynamic_width, player_text_width)

    screen = pygame.display.set_mode((dynamic_width, HEIGHT))

    running = True
    while running:
        screen.fill(WHITE)
        draw_board(board, screen, last_move)

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and move_index < len(moves):
                    last_move = moves[move_index]
                    board.push(moves[move_index])
                    move_index += 1
                    autoplay = False
                elif event.key == pygame.K_LEFT and move_index > 0:
                    move_index -= 1
                    last_move = board.pop()
                    autoplay = False

        current_time = pygame.time.get_ticks()
        if current_time - last_button_press_time > button_cooldown:
            move_index, autoplay, last_move = handle_buttons(mouse_pos, board, moves, move_index, autoplay, last_move)
            last_button_press_time = current_time

        draw_buttons(autoplay, screen)
        draw_move_list(moves, move_index, white_player, black_player, screen)

        if autoplay and move_index < len(moves):
            last_move = moves[move_index]
            board.push(moves[move_index])
            move_index += 1
            pygame.display.update()
            time.sleep(0.25)

        if move_index == len(moves):  
            font = pygame.font.SysFont(None, 100)

            result_bg_surface = pygame.Surface((400, 80))  
            result_bg_surface.set_alpha(128)  
            result_bg_surface.fill((0, 0, 0))  

            screen.blit(result_bg_surface, (75, 240))

            if result == "1-0":
                result_text = "White Won"
            elif result == "0-1":
                result_text = "Black Won"
            else:
                result_text = "Draw"
            
            result_surface = font.render(result_text, True, (250, 250, 250))  
            screen.blit(result_surface, (95, 250))  

        pygame.display.update()

pgn_file = sys.argv[1]
simulate_game(pgn_file)