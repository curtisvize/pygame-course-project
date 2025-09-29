import pygame
from random import randint

class Robot_Runner:
    def __init__(self):
        pygame.init()

        # game variables
        self.width, self.height = 640, 480
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.bg_color = (102, 107, 87)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.red = (255, 0, 0)
        self.fps = 60
        self.game_font_title = pygame.font.SysFont("Arial", 64, bold=True)
        self.game_font_large = pygame.font.SysFont("Arial", 32, bold=True)
        self.game_font_small = pygame.font.SysFont("Arial", 20, bold=True)
        self.clock = pygame.time.Clock()

        self.images = {
            "coin": pygame.image.load("coin.png"),
            "monster": pygame.image.load("monster.png"),
            "robot": pygame.image.load("robot.png")
        }

        self.points = 0
        self.game_state = "start_screen" # states are start_screen, playing, and game_over
        self.coins_number = 3
        self.monsters_number = 2
        self.coins = []
        self.monsters = []     
        self.spawn_distance_min = 100
        self.spawn_distance_max = 500
        self.gravity = 1
        self.ground = self.height - self.images["robot"].get_height()

        pygame.display.set_caption("Robot Runner")

        self.init_player()
        self.init_objects()

        self.main_loop()
    
    # init functions
    # The player is stored as a dictionary with coordinate(x, y), rect, and mask keys.
    # Coins and monsters are lists of dict objects, each having a similar data structure.
    # Rects and masks are used to aid in collision detection as these are built in to Pygame.
    def init_player(self):
        player_x, player_y = self.width * 0.01, self.ground

        self.player = {
            "x": player_x,
            "y": player_y,
            "rect": pygame.Rect(player_x, player_y, self.images["robot"].get_width(), self.images["robot"].get_height()),
            "mask": pygame.mask.from_surface(self.images["robot"])
        }

        # jump variables
        self.jumping = False
        self.holding_spacebar = False
        self.boosting_jump = False
        self.new_jump = False
        self.y_velocity = 0
        self.min_jump_power = -8
        self.max_jump_power = -200
        self.jump_power_increment = 1.2
        self.max_jump_y = self.images["coin"].get_height() - 8 # no coins should be out of reach

        # movement variables
        self.player_speed = 3
        self.min_x = 0
        self.max_x = self.width - self.images["robot"].get_width()
    
    def init_objects(self):
        self.object_speed = 2
        self.coins = [self.respawn("coin") for i in range(self.coins_number)]
        self.monsters = [self.respawn("monster") for i in range(self.monsters_number)]


    # player control functions
    def handle_jump_input(self, spacebar_pressed):
        # Here we track the state of the player's jump and a boost to the jump if the spacebar key is held down.
        # Jump movement and physics are handled in jump_physics()
        if spacebar_pressed and not self.jumping and not self.holding_spacebar:
            self.new_jump = True
            self.boosting_jump = True
            self.holding_spacebar = True

        elif not spacebar_pressed:
            self.holding_spacebar = False
            self.boosting_jump = False

    def jump_physics(self):
        if self.new_jump:
            self.jumping = True
            self.y_velocity = self.min_jump_power
            self.new_jump = False
        
        if self.jumping:
            # continue to boost the jump while in constraints
            if self.boosting_jump and self.y_velocity < 0 and self.player["y"] > self.max_jump_y:
                if self.y_velocity > self.max_jump_power:
                    self.y_velocity -= self.jump_power_increment
            
            # apply gravity for a somewhat realistic "fall"
            self.y_velocity += self.gravity

            # stop boosting the jump once velocity/gravity evens out or the player hits the max allowed height
            if self.y_velocity >= 0 or self.player["y"] <= self.max_jump_y:
                self.boosting_jump = False
            
            new_y = self.player["y"] + self.y_velocity

            # additional sanity checks to ensure the player doesn't end up above the ceiling or below the ground
            if new_y <= self.max_jump_y:
                new_y = self.max_jump_y
                self.y_velocity = 0
            
            if new_y >= self.ground:
                new_y = self.ground
                self.jumping = False
                self.y_velocity = 0
            
            return new_y

        return self.player["y"]


    # Collision functions
    # Both functions first check if a pygame rect collision has occurred, then do additional mask checking
    # for more accurate collision detection
    def check_coin_collisions(self):
        # Adds a point to the score if the player collects a coin
        for i in range(len(self.coins)):
            if self.player["rect"].colliderect(self.coins[i]["rect"]):
                offset_x = self.coins[i]["x"] - self.player["x"]
                offset_y = self.coins[i]["y"] - self.player["y"]

                if self.player["mask"].overlap(self.coins[i]["mask"], (offset_x, offset_y)):
                    self.coins[i] = self.respawn("coin")
                    self.points += 1

                    # speed ramps up when the player collects 10 coins
                    if self.points % 10 == 0 and self.points != 0:
                        self.object_speed = round(self.object_speed + 0.4, 1)
                        self.player_speed = round(self.player_speed + 0.2, 1)
    
    def check_monster_collisions(self):
        # Returns True when the player collides with a monster
        for i in range(len(self.monsters)):
            if self.player["rect"].colliderect(self.monsters[i]["rect"]):
                offset_x = self.monsters[i]["x"] - self.player["x"]
                offset_y = self.monsters[i]["y"] - self.player["y"]

                if self.player["mask"].overlap(self.monsters[i]["mask"], (offset_x, offset_y)):
                    return True
        
        return False


    # main loop and game functions
    def main_loop(self):
        while True:
            self.check_events()
            self.update_game()
            self.draw_screen()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    if self.game_state in ["start_screen", "game_over"]:
                        self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    exit()
            if event.type == pygame.QUIT:
                exit()

        if self.game_state == "playing":
            keys = pygame.key.get_pressed()

            self.handle_jump_input(keys[pygame.K_SPACE])
        
            # left and right key press state are stored to use in move_player()
            self.left = keys[pygame.K_LEFT]
            self.right = keys[pygame.K_RIGHT]

    def update_game(self):
        if self.game_state == "playing":
            jump_y = self.jump_physics()
            self.move_player(self.left, self.right, jump_y)
            
            self.move_objects()

            self.check_coin_collisions()
            if self.check_monster_collisions():
                self.game_state = "game_over"
    
    def move_player(self, left, right, jump_y):
        if left:
            self.player["x"] -= self.player_speed
            if self.player["x"] < self.min_x:
                self.player["x"] = self.min_x
        
        if right:
            self.player["x"] += self.player_speed
            if self.player["x"] > self.max_x:
                self.player["x"] = self.max_x
        
        self.player["y"] = jump_y

        self.player["rect"].x = self.player["x"]
        self.player["rect"].y = self.player["y"]
    
    def move_objects(self):
        # move non-player objects
        for i in range(len(self.coins)):
            self.coins[i]["x"] -= self.object_speed
            self.coins[i]["rect"].x = self.coins[i]["x"]

            # edge of screen respawn
            if self.coins[i]["x"] + self.images["coin"].get_width() < 0:
                self.coins[i] = self.respawn("coin")
        
        for i in range(len(self.monsters)):
            self.monsters[i]["x"] -= self.object_speed
            self.monsters[i]["rect"].x = self.monsters[i]["x"]

            # respawn
            if self.monsters[i]["x"] + self.images["monster"].get_width() < 0:
                self.monsters[i] = self.respawn("monster")
        
    def respawn(self, object: str):
        # Respawns coins and monsters at random locations off-screen to the right
        # The function expects "coin" or "monster" for the object variable so we can get the correct image dimensions
        while True:
            x = randint(self.width + self.spawn_distance_min, self.width + self.spawn_distance_max)
            y = randint(0, self.height - self.images[object].get_height())
            new_rect = pygame.Rect(x, y, self.images[object].get_width(), self.images[object].get_height())

            if not self.check_overlap(new_rect):
                break

        new_object = {
            "x": x,
            "y": y,
            "rect": new_rect,
            "mask": pygame.mask.from_surface(self.images[object])
        }

        return new_object
        
    def check_overlap(self, new_rect):
        # returns False only if the new rect doesn't collide with any others
        for coin in self.coins:
            if new_rect.colliderect(coin["rect"]):
                return True
            
        for monster in self.monsters:
            if new_rect.colliderect(monster["rect"]):
                return True
        
        return False
    
    def reset_game(self):
        self.points = 0
        self.game_state = "playing"

        self.init_player()
        self.init_objects()

    
    # draw functions
    def draw_screen(self):
        self.screen.fill(self.bg_color)
        self.draw_objects()

        if self.game_state == "start_screen":
            self.draw_start_screen()
        elif self.game_state == "playing":
            self.draw_score()
        else:
            self.draw_game_over_screen()

        pygame.display.flip()

        self.clock.tick(self.fps)
    
    def draw_objects(self):
        # player
        self.screen.blit(self.images["robot"], (self.player["x"], self.player["y"]))

        # coins and monsters
        for coin in self.coins:
            self.screen.blit(self.images["coin"], (coin["x"], coin["y"]))
        for monster in self.monsters:
            self.screen.blit(self.images["monster"], (monster["x"], monster["y"]))

    def draw_score(self):
        score_text = self.game_font_small.render(f"Points: {self.points}", True, self.white)
        score_rect = score_text.get_rect()
        score_rect.topright = (self.width - 10, 10)
        self.screen.blit(score_text, score_rect)
    
    def draw_start_screen(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((self.black))
        self.screen.blit(overlay, (0, 0))

        title_text = self.game_font_title.render("Robot Runner", True, self.red)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 4))
        self.screen.blit(title_text, title_rect)

        instructions_text = [
            "Collect Coins, Avoid Monsters",
            "The Higher Your Score, The Faster Things Move",
            "How Many Points Can You Get?"
        ]

        start_y = self.height // 4 + 50
        for i in range(len(instructions_text)):
            text = self.game_font_small.render(instructions_text[i], True, self.white)
            text_rect = text.get_rect(center=(self.width // 2, start_y + i * 25))
            self.screen.blit(text, text_rect)

        controls_header_text = self.game_font_large.render("Controls:", True, self.white)
        controls_header_rect = controls_header_text.get_rect(center=(self.width // 2, self.height // 4 + 180))
        self.screen.blit(controls_header_text, controls_header_rect)

        controls_text = [
            "Left and Right Arrow Keys: Move Left and Right",
            "Spacebar: Jump (hold to jump higher)",
            "N: Start New Game",
            "ESC: Quit"
        ]

        start_y = self.height // 2 + 100
        for i in range(len(controls_text)):
            text = self.game_font_small.render(controls_text[i], True, self.white)
            text_rect = text.get_rect(center=(self.width // 2, start_y + i * 25))
            self.screen.blit(text, text_rect)
    
    def draw_game_over_screen(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((self.black))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.game_font_title.render("GAME OVER", True, self.red)
        game_over_rect = game_over_text.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(game_over_text, game_over_rect)

        score_text = self.game_font_large.render(f"Final Score: {self.points}", True, self.white)
        score_rect = score_text.get_rect(center=(self.width // 2, self.height // 3 + 50))
        self.screen.blit(score_text, score_rect)

        restart_text = self.game_font_small.render(f"Press N for New Game or ESC to Quit", True, self.white)
        restart_rect = restart_text.get_rect(center=(self.width // 2, self.height // 2 + 100))
        self.screen.blit(restart_text, restart_rect)

if __name__ == "__main__":
    Robot_Runner()
