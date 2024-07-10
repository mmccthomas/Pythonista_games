from UI import scrabble_renderer
from Game import scrabble_game, scrabble_objects
import pygame as p

mode = 'en'


if mode == 'en':
    gamestate = scrabble_game.GameState('Data/multipliers.txt', 'Data/lang/en/tiles.txt')
    gameengine = scrabble_game.GameEngine(gamestate, 'Data/lang/en/850_ogdens_words.txt')
elif mode == 'tr':
    gamestate = scrabble_game.GameState('Data/multipliers.txt', 'Data/lang/tr/tiles.txt')
    gameengine = scrabble_game.GameEngine(gamestate, 'Data/lang/tr/1000_turkishtextbook_words.txt')

renderer = scrabble_renderer.Renderer(gamestate, gameengine)

p.init()

# Create a window with a resolution of 680x480
screen = p.display.set_mode((scrabble_renderer.WINDOW_WIDTH, scrabble_renderer.WINDOW_HEIGHT))

renderer.init_pymenus()
renderer.init_location_rects()

clock = p.time.Clock()

dragging = False
drag_mode_board = False
drag_old_pos = (-1, -1)
dragging_tile = None
drag_surf = p.Surface((scrabble_renderer.SQ_SIZE, scrabble_renderer.SQ_SIZE))        

# Main loop
running = True
while running:
    events = p.event.get()
    game_surf = p.Surface((scrabble_renderer.WINDOW_WIDTH, scrabble_renderer.WINDOW_HEIGHT))           

    renderer.ai_opt_btn_sec.update(events)
    renderer.ai_possible_moves_sec.update(events)
    renderer.player_btn_sec.update(events)
    renderer.render_game(game_surf)

    # Handle events
    for event in events:
        if event.type == p.QUIT:
            running = False
        elif event.type == p.MOUSEBUTTONDOWN:
            if gamestate.p1_to_play:
                if not renderer.swap_mode:
                    if event.button == 1:
                        board_is_col, board_tile = renderer.board_col_detect(*event.pos)
                        rack_is_col, rack_tile = renderer.rack_col_detect(*event.pos)
                        if board_is_col or rack_is_col:
                                if board_is_col:
                                    cell = gamestate.board.board[board_tile[0]][board_tile[1]]
                                    tile_to_drag = cell.tile
                                    if tile_to_drag != None and tile_to_drag.draft:
                                        cell.tile = None
                                        dragging = True
                                        drag_mode_board = True
                                        drag_old_pos = board_tile
                                        dragging_tile = tile_to_drag

                                if rack_is_col:
                                    tile_to_drag = gamestate.player_1.rack.tiles[rack_tile]
                                    if tile_to_drag != None and not tile_to_drag.draft:
                                        dragging = True
                                        drag_mode_board = False
                                        drag_old_pos = rack_tile
                                        dragging_tile = tile_to_drag

                                        dragging_tile.draft = True
                    if event.button == 3:
                        board_is_col, board_tile = renderer.board_col_detect(*event.pos)
                        if board_is_col:
                            cell = gamestate.board.board[board_tile[0]][board_tile[1]]
                            tile = cell.tile
                            if tile != None and tile.draft:
                                cell.tile = None
                                tile.draft = False
                else:
                    if event.button == 1:
                        rack_is_col, rack_tile = renderer.rack_col_detect(*event.pos)
                        if rack_is_col:
                            tile_to_drag = gamestate.player_1.rack.tiles[rack_tile]
                            if tile_to_drag != None:
                                tile_to_drag.draft = not tile_to_drag.draft            
        elif event.type == p.MOUSEBUTTONUP:
            if gamestate.p1_to_play:
                if not renderer.swap_mode:
                    if event.button == 1:
                        if dragging:
                            if not drag_mode_board:
                                board_is_col, board_tile = renderer.board_col_detect(*event.pos)
                                if not board_is_col:
                                    dragging_tile.draft = False
                                    dragging = False
                                else:
                                    cell = gamestate.board.board[board_tile[0]][board_tile[1]]
                                    cell.tile = dragging_tile
                                    dragging = False
                            else:
                                board_is_col, board_tile = renderer.board_col_detect(*event.pos)
                                if board_is_col:
                                    board_is_col, board_tile = renderer.board_col_detect(*event.pos)
                                    cell = gamestate.board.board[board_tile[0]][board_tile[1]]
                                    if cell.tile == None:
                                        cell.tile = dragging_tile
                                        dragging = False
                                    else:
                                        old_cell = gamestate.board.board[drag_old_pos[0]][drag_old_pos[1]]
                                        old_cell.tile = dragging_tile
                                        dragging = False
                                else:
                                        old_cell = gamestate.board.board[drag_old_pos[0]][drag_old_pos[1]]
                                        old_cell.tile = dragging_tile
                                        dragging = False

    if dragging:
        renderer.render_tile(dragging_tile, drag_surf)
        game_surf.blit(drag_surf, (event.pos[0] - scrabble_renderer.SQ_SIZE // 2, event.pos[1] - scrabble_renderer.SQ_SIZE // 2))

    screen.blit(game_surf, (0, 0))

    p.display.flip()

    clock.tick(scrabble_renderer.MAX_FPS)

p.quit()
