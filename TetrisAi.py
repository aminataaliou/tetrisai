import pygame
import random
import copy

colors = [
    (0, 0, 0),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]


class Figure:
    x = 0
    y = 0

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
    ]

    def __init__(self, x, y):
        self.x = x  # x horizontal position
        self.y = y  # y vertical position
        self.type = random.randint(0, len(self.figures) - 1)  # random choice of the tetris shape to use
        self.color = random.randint(1, len(colors) - 1)  # random color choice
        self.rotation = 0  # tetris figure set to default rotation

    def image(self):
        return self.figures[self.type][self.rotation % len(self.figures[self.type])]
    
    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])

    @property
    def rotation_count(self):
        return len(self.figures[self.type])


class Tetris:
    def __init__(self, height, width):
        self.level = 1  # starting difficulty
        self.score = 0  # player initial score
        self.state = "start"
        self.field = []  # 2-D grid
        self.height = 0
        self.width = 0
        self.x = 100
        self.y = 60
        self.zoom = 20
        self.figure = None  # current falling tetris piece

        self.height = height
        self.width = width
        self.field = []
        self.score = 0
        self.state = "start"
        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):  # creation of brand new falling tetris piece
        self.figure = Figure(3, 0)  # with a horizontal position of x=3 and a vertical one of y=0 -> top of board

    def intersects(self):  # determining whether the current falling piece collides with bottom of board, left or right wall, existing blocks
        intersection = False

        # looping through a 4x4 grid
        for i in range(4):
            for j in range(4):
                # having each cell have a number from 0 to 15 for indexing
                if i * 4 + j in self.figure.image():

                    # check for collision
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True  # any collision detected true is returned
        return intersection

    # removing the completed lines
    def break_lines(self):
        lines = 0  # tracking cleared lines
        for i in range(1, self.height):  # loop through each row
            zeros = 0  # initializing the zeros in a row
            for j in range(self.width):  # counting the zeros per row
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:  # if there are no zeros increment number of cleared lines
                lines += 1
                for i1 in range(i, 1, -1):  # shifting rows downward
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        self.score += lines ** 2  # updating score

    def go_space(self):  # moving pieces straight down until it hits something
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1  # moving the tetris piece back up one row
        self.freeze()

    def go_down(self):  # soft drop by moving the piece down by a row at a time
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):  # locking piece position in the board
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_side(self, dx):  # moving piece to the left or to the right
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):  # rotating piece
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation


def evaluate_field(field):
    height = len(field)
    width = len(field[0])
    
    holes = 0
    heights = [0] * width
    
    # evaluating height of blocks so that ai avoid tall uneven stacks, counts holes too
    for x in range(width):
        block_found = False
        for y in range(height):
            if field[y][x] != 0:
                if not block_found:
                    heights[x] = height - y
                    block_found = True
                elif block_found:
                    holes += 1
    
    aggregate_height = sum(heights)
    bumpiness = sum(abs(heights[i] - heights[i+1]) for i in range(width-1))
    
    return (
        -0.5 * aggregate_height
        -0.7 * holes
        -0.3 * bumpiness)


def get_ai_suggestions(game, top_n=3):
    suggestions = []
    if game.figure is None:
        return suggestions
        
    original_x = game.figure.x
    original_y = game.figure.y
    original_rot = game.figure.rotation  # saving original piece state
    
    # trying every rotation (1-4 possible rotations)
    for rotation in range(len(Figure.figures[game.figure.type])):
        game.figure.rotation = rotation
        
        for x in range(-2, game.width + 1):  # trying every horizontal position
            game.figure.x = x
            game.figure.y = 0
            
            # Move down until collision
            while not game.intersects():
                game.figure.y += 1
            game.figure.y -= 1
            
            # Skip invalid placements (above the board)
            if game.figure.y < 0:
                continue
            
            # Create a copy of the field to simulate placement
            temp_field = copy.deepcopy(game.field)
            
            # Place the piece in the temporary field
            placed_successfully = True
            for i in range(4):
                for j in range(4):
                    if i * 4 + j in game.figure.image():
                        temp_y = i + game.figure.y
                        temp_x = j + game.figure.x
                        if 0 <= temp_y < game.height and 0 <= temp_x < game.width:
                            temp_field[temp_y][temp_x] = game.figure.color
                        else:
                            placed_successfully = False
            
            if placed_successfully:
                score = evaluate_field(temp_field)
                suggestions.append((score, x, rotation, game.figure.y))

    # Restoring original state
    game.figure.x = original_x
    game.figure.y = original_y
    game.figure.rotation = original_rot

    # Sorting and returning the best moves
    suggestions.sort(reverse=True, key=lambda s: s[0])
    return suggestions[:top_n]


# Initialization game engine
pygame.init()

# Definition of some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

size = (400, 500)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Tetris")

# Loop until the user clicks the close button.
done = False
clock = pygame.time.Clock()
fps = 30
game = Tetris(20, 10)
counter = 0

pressing_down = False

while not done:
    if game.figure is None:
        game.new_figure()
    counter += 1
    if counter > 100000:
        counter = 0

    if counter % (fps // game.level // 1) == 0 or pressing_down:
        if game.state == "start":
            game.go_down()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
            if event.key == pygame.K_DOWN:
                pressing_down = True
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
            if event.key == pygame.K_SPACE:
                game.go_space()
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    screen.fill(WHITE)
    

    # Game board drawing
    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen, GRAY, [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom], 1)
            if game.field[i][j] > 0:
                pygame.draw.rect(screen, colors[game.field[i][j]],
                                 [game.x + game.zoom * j + 1, game.y + game.zoom * i + 1, game.zoom - 2, game.zoom - 1])

    # Get then dispaly AI suggestions
    if game.figure is not None and game.state == "start":
        suggestions = get_ai_suggestions(game, top_n=3)
        
        # Draw AI suggestions as transparent previews
        for idx, (score, x, rot, final_y) in enumerate(suggestions):
            # Draw preview of where piece would land
            for i in range(4):
                for j in range(4):
                    if i * 4 + j in Figure.figures[game.figure.type][rot]:
                        # Calculate position
                        draw_x = game.x + game.zoom * (j + x)
                        draw_y = game.y + game.zoom * (i + final_y)
                        
                        # Draw a semi-transparent preview
                        s = pygame.Surface((game.zoom - 2, game.zoom - 2), pygame.SRCALPHA)
                        color_idx = (idx + 1) % (len(colors) - 1) + 1
                        # Make it more transparent for better visibility
                        preview_color = (*colors[color_idx][:3], 80)  # More transparent (80 instead of 100)
                        s.fill(preview_color)
                        screen.blit(s, (draw_x + 1, draw_y + 1))
                        
                        # Draw outline
                        pygame.draw.rect(screen, colors[color_idx],
                                         [draw_x, draw_y, game.zoom, game.zoom], 1)

    # Draw the current falling piece
    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color],
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                      game.y + game.zoom * (i + game.figure.y) + 1,
                                      game.zoom - 2, game.zoom - 2])

    # Drawing UI
    font = pygame.font.SysFont('Calibri', 25, True, False)
    font1 = pygame.font.SysFont('Calibri', 65, True, False)
    text = font.render("Score: " + str(game.score), True, BLACK)
    
    # AI Advice Text
    if game.figure is not None and game.state == "start":
        suggestions = get_ai_suggestions(game, top_n=1)
        if suggestions:
            best_score, best_x, best_rot, best_y = suggestions[0]
            advice_text = font.render(f"AI: Move to X={best_x}", True, (0, 100, 0)) #best AI suggestion is in green
            screen.blit(advice_text, [0, 30])
    
    screen.blit(text, [0, 0])
    
    if game.state == "gameover":
        text_game_over = font1.render("Game Over", True, (255, 125, 0))
        text_game_over1 = font1.render("Press ESC", True, (255, 215, 0))
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()