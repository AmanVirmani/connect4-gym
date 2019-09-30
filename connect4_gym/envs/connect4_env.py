import gym
from gym import spaces, error
import numpy as np
from PIL import Image, ImageDraw
import pygame


class Board(object):
    class InvalidMove(Exception):
        pass

    class NoSpaceOnColumn(InvalidMove):
        pass

    class InvalidColumnValue(InvalidMove):
        pass

    class ColumnOutOfRange(InvalidMove):
        pass

    class GameAlreadyEnded(InvalidMove):
        pass

    BOARD_WIDTH = 7
    BOARD_HEIGHT = 6

    def __init__(self):
        self.board = np.zeros((6, 7), dtype=int)
        self.column_fill = np.zeros(7, dtype=int)
        self.player = 1
        self.finished = False

    def reset(self):
        self.board.fill(0)
        self.column_fill.fill(0)
        self.finished = 0
        self.player = 1

    def _validate_move(self, column):
        if not isinstance(column, int):
            raise Board.InvalidColumnValue()

        if column < 0 or self.board.shape[1] <= column:
            raise Board.ColumnOutOfRange()

        if self.column_fill[column] == self.board.shape[0]:
            raise Board.NoSpaceOnColumn()

        if self.finished:
            raise Board.GameAlreadyEnded()

    def get_current_player(self):
        return self.player

    def _check_finish(self, row, column):
        """
        /*   #  #  #
         *    # # #
         *     ###
         *   #######
         *     ###
         *    # # #
         *   #  #  #
         */
        :param row:
        :param column:
        :return:
        """
        row_step    = [ 0, -1, -1, -1]
        column_step = [ 1,  1,  0, -1]

        for direction in range(4):
            for backwards_move in range(4):
                starting_row = row - backwards_move * row_step[direction]
                starting_column = column - backwards_move * column_step[direction]

                players = [0, 0, 0]
                for step in range(4):
                    current_row = starting_row + step * row_step[direction]
                    current_column = starting_column + step * column_step[direction]

                    if 0 <= current_row < self.board.shape[0] and 0 <= current_column < self.board.shape[1]:
                        players[self.board[current_row, current_column]] += 1

                if players[1] == 4 or players[2] == 4:
                    return True

        return False

    def place(self, column):
        self._validate_move(column)

        self.board[self.column_fill[column], column] = self.player
        self.column_fill[column] += 1

        self.player = 3 - self.player

        self.finished = self._check_finish(self.column_fill[column] - 1, column)
        return self.finished


class Color(object):
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)


def render_board(board,
                 image_width=512,
                 image_height=512,
                 board_percent_x=0.8,
                 board_percent_y=0.8,
                 items_padding_x=0.05,
                 items_padding_y=0.05,
                 slot_padding_x=0.1,
                 slot_padding_y=0.1,
                 background_color=Color.WHITE,
                 board_color=Color.BLUE,
                 empty_slot_color=Color.WHITE,
                 player1_slot_color=Color.RED,
                 player2_slot_color=Color.YELLOW):
    image = Image.new('RGB', (image_height, image_width), background_color)
    draw = ImageDraw.Draw(image)

    board_width = int(image_width * board_percent_x)
    board_height = int(image_height * board_percent_y)

    padding_x = image_width - board_width
    padding_y = image_height - board_height

    padding_top = padding_y // 2
    padding_bottom = padding_y - padding_top

    padding_left = padding_x // 2
    padding_right = padding_x - padding_left

    draw.rectangle([
        (padding_left, padding_top),
        (image_width - padding_right, image_height - padding_bottom)
    ], fill=board_color)

    padding_left += int(items_padding_x * image_width)
    padding_right += int(items_padding_x * image_width)

    padding_top += int(items_padding_y * image_height)
    padding_bottom += int(items_padding_y * image_height)

    cage_width = int((image_width - padding_left - padding_right) / board.shape[1])
    cage_height = int((image_width - padding_top - padding_bottom) / board.shape[0])

    radius_x = int((cage_width - 2 * int(cage_width * slot_padding_x)) // 2)
    radius_y = int((cage_height - 2 * int(cage_height * slot_padding_y)) // 2)

    slots = []
    for row in range(board.shape[0]):
        for column in range(board.shape[1]):
            player = board[row, column]

            actual_row = board.shape[0] - row - 1
            origin_x = padding_left + int(column * cage_width + cage_width // 2)
            origin_y = padding_top + int(actual_row * cage_height + cage_height // 2)

            slots.append((origin_x, origin_y, player))

    for origin_x, origin_y, player in slots:
        color = empty_slot_color
        if player == 1:
            color = player1_slot_color
        elif player == 2:
            color = player2_slot_color

        draw.ellipse([
            (origin_x - radius_x, origin_y - radius_y),
            (origin_x + radius_x, origin_y + radius_y)
        ], fill=color)

    return np.array(image)


class Connect4Env(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human', 'console']}

    def __init__(self, window_width=512, window_height=512):
        super(Connect4Env, self).__init__()

        self.action_space = spaces.Discrete(7)

        self.window_width = window_width
        self.window_height = window_height
        self.observation_space = spaces.Box(low=0, high=255, shape=(window_height, window_width, 3))
        self.screen = None
        self.rendered_board = None
        self.board = Board()

    def _update_board_render(self):
        self.rendered_board = render_board(self.board.board,
                                           image_width=self.window_width,
                                           image_height=self.window_height)

    def step(self, action):
        try:
            player = self.board.get_current_player()
            finished = self.board.place(action)
            self._update_board_render()
        except Board.InvalidMove as e:
            raise error.InvalidAction(repr(e))

        return self.rendered_board, 1 if finished else 0, finished, {
            'board': self.board.board.tolist(),
            'last_player': player
        }

    def reset(self):
        self.board.reset()
        self._update_board_render()

        return self.rendered_board

    def render(self, mode='human', close=False):
        if mode == 'console':
            print(np.flip(self.board.board, axis=0))
        elif mode == 'human':
            if self.screen is None:
                pygame.init()
                self.screen = pygame.display.set_mode((round(self.window_width), round(self.window_height)))

            if close:
                pygame.quit()

            frame = render_board(self.board.board)
            surface = pygame.surfarray.make_surface(frame)
            surface = pygame.transform.rotate(surface, -90)
            surface = pygame.transform.flip(surface, True, False)
            self.screen.blit(surface, (0, 0))

            pygame.display.update()
        else:
            raise error.UnsupportedMode()

    def close(self):
        pygame.quit()
