from Game.scrabble_objects import *
from Game.scrabble_game import *

import pygame as p
import pygame_menu as pm

WINDOW_HEIGHT = 750
WINDOW_WIDTH = 1250

BOARD_WIDTH = BOARD_HEIGHT = 750
DIMENSION = 15
LINE_WIDTH = 2
MAX_FPS = 30
SQ_SIZE = BOARD_WIDTH // DIMENSION

class Renderer():

    def __init__(self, gamestate, gameengine):
        self.gamestate = gamestate
        self.gameengine = gameengine
        self.swap_mode = False

    def handle_play_button(self):
        print("Play clicked.")
        if not self.swap_mode:
            self.gameengine.play_draft()

    def handle_swap_button(self):
        if not self.swap_mode:
            is_able_to_swap = True
            for tile in self.gamestate.player_1.rack.tiles:
                if tile.draft:
                    is_able_to_swap = False
                    break
            if is_able_to_swap:
                self.swap_mode = not self.swap_mode
        else:
            if self.gameengine.swap_draft():
                self.swap_mode = not self.swap_mode

    def handle_ai_play_button(self):
        self.gameengine.ai_make_move()

    def handle_autoplay_button(self):
        self.gameengine.autoplay = not self.gameengine.autoplay

    def on_change(self, option_item):
        self.gameengine.clear_draft()
        for cell, tile in self.gameengine.ai_possible_moves[option_item[1]].items():
            cell.tile = tile
            tile.draft = True

    def handle_play_selection_button(self):
        drop_down_widget = self.ai_possible_moves_sec.get_widget('poss_moves')
        _, selected_idx = drop_down_widget.get_value()

        if selected_idx != -1:
            self.gameengine.play_option(selected_idx)
        
        drop_down_widget.reset_value()
        drop_down_widget.update_items([])

    def init_pymenus(self):
        theme = pm.Theme(
            background_color=pm.themes.TRANSPARENT_COLOR,
            title=False,
            widget_font=pm.font.FONT_FIRACODE,
            widget_font_color=(255, 255, 255),
            # widget_margin=(0, 15),
            widget_selection_effect=pm.widgets.NoneSelection()
        )

        self.player_btn_sec = pm.Menu('', 300, 40, theme=theme, rows=1, columns=2, position=(850, 120, False))
        play_btn = self.player_btn_sec.add.button("  PLAY  ", lambda: self.handle_play_button(), button_id = "play", background_color = p.Color(44, 0, 0), font_size=20, shadow_width=10)
        swap_btn = self.player_btn_sec.add.button("  SWAP  ", lambda: self.handle_swap_button(), button_id = "swap", background_color = p.Color(44, 0, 0), font_size=20, shadow_width=10)
        play_btn.resize(120, 40, True)
        swap_btn.resize(120, 40, True)
        
        self.ai_opt_btn_sec = pm.Menu('', 300, 40, theme=theme, rows=1, columns=2, position=(850, 230, False))
        ai_play_btn = self.ai_opt_btn_sec.add.button("AI PLAY", lambda: self.handle_ai_play_button(), button_id = "ai_play", background_color = p.Color(44, 0, 0), font_size=20, shadow_width=10)
        autoplay_btn = self.ai_opt_btn_sec.add.button("AUTOPLAY", lambda: self.handle_autoplay_button(), button_id = "autoplay", background_color = p.Color(44, 0, 0), font_size=20, shadow_width=10)
        ai_play_btn.resize(120, 40, True)
        autoplay_btn.resize(120, 40, True)
        
        self.ai_possible_moves_sec = pm.Menu('', 400, 320, theme=theme, rows=3, columns=1, position=(800, 430, False))

        self.ai_possible_moves_sec.add.dropselect(title='',
            items=['---'],
            onchange=self.on_change,
            dropselect_id='poss_moves',
            font_size=16,
            padding=0,
            placeholder='Select one',
            selection_box_height=5,
            selection_box_inflate=(0, 20),
            selection_box_margin=0,
            selection_box_text_margin=10,
            selection_box_width=400,
            selection_option_font_size=20,
            shadow_width=20,
            margin=(0, 10))
        
        console_surf = p.Surface((375, 200))
        self.ai_possible_moves_sec.add.surface(console_surf)

        selected_play_btn = self.ai_possible_moves_sec.add.button("PLAY SELECTION", lambda: self.handle_play_selection_button(), button_id = "selected_play", background_color = p.Color(44, 0, 0), font_size=20, shadow_width=10)
        selected_play_btn.resize(120, 40, True)
  
    def rack_col_detect(self, x, y):
        for i in range(7):
            if self.rack_rects[i].collidepoint(x, y):
                return True, i
        return False, -1
            
    def board_col_detect(self, x, y):
        for i in range(15):
            for j in range(15):
                if self.board_rects[i][j].collidepoint(x, y):
                    return True, (i, j)
        return False, (-1, -1)

    def init_location_rects(self):
        self.rack_rects = []
        for i in range(7):
            self.rack_rects.append(p.Rect(825 + i * SQ_SIZE, 50, SQ_SIZE, SQ_SIZE))

        self.board_rects = []
        for i in range(15):
            row = []
            for j in range(15):
                start_pos_y = i * SQ_SIZE
                start_pos_x = j * SQ_SIZE
                row.append(p.Rect(start_pos_x, start_pos_y, SQ_SIZE, SQ_SIZE))
            self.board_rects.append(row)

    def render_game(self, surf):

        surf_rect = surf.get_rect()

        surf.fill((220, 220, 220))

        gameboard_surf = p.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        self.render_board(self.gamestate.board, gameboard_surf)
        surf.blit(gameboard_surf, (0, 0))


        font_12 = p.font.Font('freesansbold.ttf', 12)

        rendered_text = font_12.render("PLAYER - {}".format(self.gamestate.player_1.score), True, (0, 0, 0))
        surf.blit(rendered_text, (760, 10))

        rendered_text = font_12.render("{} - AI".format(self.gamestate.player_2.score), True, (0, 0, 0))
        surf.blit(rendered_text, (1200, 10))

        font_16 = p.font.Font('freesansbold.ttf', 16)
        rendered_text = font_16.render("PLAYER RACK", True, (0, 0, 0))
        surf.blit(rendered_text, (940, 20))

        rack1_surf = p.Surface((SQ_SIZE * 7, SQ_SIZE))
        self.render_rack(self.gamestate.player_1.rack, rack1_surf)
        surf.blit(rack1_surf, (825, 50))

        self.player_btn_sec.get_widget('swap').update_font({'color':((0, 255, 0) if self.swap_mode else (255, 255, 255))})
        self.player_btn_sec.draw(surf)

        p.draw.line(surf, (0, 0, 0), (BOARD_WIDTH, 190), (WINDOW_WIDTH, 190), 2)

        rendered_text = font_16.render("AI", True, (0, 0, 0))
        surf.blit(rendered_text, (990, 200))

        self.ai_opt_btn_sec.get_widget('autoplay').update_font({'color':((0, 255, 0) if self.gameengine.autoplay else (255, 255, 255))})
        self.ai_opt_btn_sec.draw(surf)

        p.draw.line(surf, (0, 0, 0), (BOARD_WIDTH, 290), (WINDOW_WIDTH, 290), 2)

        rendered_text = font_16.render("AI RACK", True, (0, 0, 0))
        surf.blit(rendered_text, (965, 310))

        rack2_surf = p.Surface((SQ_SIZE * 7, SQ_SIZE))
        self.render_rack(self.gamestate.player_2.rack, rack2_surf)
        surf.blit(rack2_surf, (825, 340))

        rendered_text = font_16.render("POSSIBLE MOVES", True, (0, 0, 0))
        surf.blit(rendered_text, (925, 410))
        
        if len(self.gameengine.ai_possible_move_ids) > 0:
            self.ai_possible_moves_sec.get_widget('poss_moves').update_items(self.gameengine.ai_possible_move_ids)
            self.gameengine.ai_possible_move_ids.clear()

        self.ai_possible_moves_sec.draw(surf)
            
        line_y = 510
        for line in self.gameengine.logs[-12:]:
            rendered_text = font_12.render(line, True, (255, 255, 255))
            surf.blit(rendered_text, (820, line_y))
            line_y += 15

    def render_board(self, board, surf):

        for i in range(DIMENSION):
            for j in range(DIMENSION):

                start_pos_y = i * SQ_SIZE
                start_pos_x = j * SQ_SIZE

                cell_surf = p.Surface((SQ_SIZE, SQ_SIZE))

                self.render_cell(board.board[i][j], cell_surf)

                surf.blit(cell_surf, (start_pos_x, start_pos_y))

        
        for i in range(DIMENSION):
            start_pos = i * SQ_SIZE
            p.draw.line(surf, (0, 0, 0), (start_pos, 0), (start_pos, BOARD_HEIGHT), LINE_WIDTH)
            p.draw.line(surf, (0, 0, 0), (0, start_pos), (BOARD_WIDTH, start_pos), LINE_WIDTH)

        p.draw.line(surf, (0, 0, 0), (DIMENSION * SQ_SIZE - LINE_WIDTH, 0), (DIMENSION * SQ_SIZE - LINE_WIDTH, BOARD_HEIGHT), LINE_WIDTH)
        p.draw.line(surf, (0, 0, 0), (0, DIMENSION * SQ_SIZE - LINE_WIDTH), (BOARD_WIDTH, DIMENSION * SQ_SIZE - LINE_WIDTH), LINE_WIDTH)

    def render_cell(self, cell, surf):

        cell_surf = surf
        cell_surf_rect = surf.get_rect()
        size = cell_surf_rect.size

        if cell.tile != None:
            self.render_tile(cell.tile, surf)
        elif cell.position == (7, 7):
            cell_surf.fill((245, 172, 179))
            cell_surf.blit(p.transform.scale(p.image.load("Data/star.png"), size), cell_surf_rect)
        else:
            font = p.font.Font('freesansbold.ttf', 10)
            multiplier = cell.multiplier

            if multiplier == 'DL':
                splitted_text = ['DOUBLE', 'LETTER', 'SCORE']
                color = (185, 211, 231)
            elif multiplier == 'TL':
                splitted_text = ['TRIPLE', 'LETTER', 'SCORE']
                color = (90, 177, 231)
            elif multiplier == 'DW':
                splitted_text = ['DOUBLE', 'WORD', 'SCORE']
                color = (245, 172, 179)
            elif multiplier == 'TW':
                splitted_text = ['TRIPLE', 'WORD', 'SCORE']
                color = (230, 61, 64)
            else:
                splitted_text = []
                color = (199, 183, 154)

            cell_surf.fill(color)

            font_linesize = font.get_linesize()
            offset = -1
            for t in splitted_text:
                rendered_text = font.render(t, True, (0, 0, 0))
                rendered_text_rect = rendered_text.get_rect()
                rendered_text_rect.center = cell_surf_rect.center
                rendered_text_rect.y += offset * font_linesize
                cell_surf.blit(rendered_text, rendered_text_rect)
                offset += 1

    def render_tile(self, tile, surf):

        surf_rect = surf.get_rect()
        size = surf_rect.size

        surf.fill((255, 255 ,255))

        font = p.font.Font('freesansbold.ttf', 24)
        rendered_text = font.render(tile.letter, True, (0, 0, 0))
        rendered_text_rect = rendered_text.get_rect()
        rendered_text_rect.center = surf_rect.center
        surf.blit(rendered_text, rendered_text_rect)

        font = p.font.Font('freesansbold.ttf', 20)
        rendered_text = font.render(str(tile.point), True, (0, 0, 0))
        rendered_text_rect = rendered_text.get_rect()
        rendered_text_rect.center = surf_rect.center
        rendered_text_rect.bottom = size[1]
        rendered_text_rect.right = size[0] - 3
        surf.blit(rendered_text, rendered_text_rect)

    def render_rack(self, rack, surf):
        surf_rect = surf.get_rect()

        p.draw.rect(surf, (128,128,128), surf.get_rect())
    
        for i in range(7):
            start_pos_x = SQ_SIZE * i
            if rack.tiles[i] != None:
                rect_surf = p.Surface((SQ_SIZE, SQ_SIZE))
                self.render_tile(rack.tiles[i], rect_surf)
                if rack.tiles[i].draft:
                    rect_surf.set_alpha(30)
                surf.blit(rect_surf, (start_pos_x, 0))


        for i in range(7):
            start_pos = i * SQ_SIZE
            p.draw.line(surf, (0, 0, 0), (start_pos, 0), (start_pos, SQ_SIZE), LINE_WIDTH)
        p.draw.line(surf, (0, 0, 0), (7 * SQ_SIZE - LINE_WIDTH, 0), (7 * SQ_SIZE - LINE_WIDTH, SQ_SIZE), LINE_WIDTH)

        p.draw.line(surf, (0, 0, 0), surf_rect.topleft, surf_rect.topright)
        
        p.draw.line(surf, (0, 0, 0), (surf_rect.bottomleft[0], surf_rect.bottomleft[1] - LINE_WIDTH), (surf_rect.bottomright[0], surf_rect.bottomright[1] - LINE_WIDTH), LINE_WIDTH)

    def render_buttons(self, surf):

        surf_rect = surf.get_rect()
