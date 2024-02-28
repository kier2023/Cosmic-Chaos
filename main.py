import pygame, sys
import random
import asyncio

WIDTH, HEIGHT = 864, 936
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cosmic Chaos")

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

PLAYER_SHIP = pygame.image.load('Assets/Visual Assets/player main.png')
PLAYER_LASER = pygame.image.load('Assets/Visual Assets/yellow laser.png')
RED_SPACESHIP = pygame.image.load('Assets/Visual Assets/red ufo.png')
GREEN_SPACESHIP = pygame.image.load('Assets/Visual Assets/green ufo.png')
BLUE_SPACESHIP = pygame.image.load('Assets/Visual Assets/blue ufo.png')

RED_LASER = pygame.image.load('Assets/Visual Assets/red laser.png')
GREEN_LASER = pygame.image.load('Assets/Visual Assets/green laser.png')
BLUE_LASER = pygame.image.load('Assets/Visual Assets/blue laser.png')
BACKGROUND = pygame.transform.scale(pygame.image.load('Assets/Visual Assets/bg.png'), (WIDTH, HEIGHT))

UNMUTE = pygame.image.load('Assets/Visual Assets/unmute.png')
MUTE = pygame.image.load('Assets/Visual Assets/mute.png')

LASER_SOUND = pygame.mixer.Sound('Assets/Audio Assets/laser-gun-shot-sound-future-sci-fi-lazer-wobble-chakongaudio-174883.wav')
pygame.mixer.music.load('Assets/Audio Assets/background_music (2).wav')

class MuteButton:
    def __init__(self):
        self.mute_icon = pygame.transform.scale(UNMUTE, (50, 50)) 
        self.unmute_icon = pygame.transform.scale(MUTE, (50, 50)) 
        self.is_muted = False

    def toggle_mute(self):
        self.is_muted = not self.is_muted

        pygame.mixer.music.set_volume(0.0 if self.is_muted else 0.1)
        LASER_SOUND.set_volume(0.0 if self.is_muted else 0.1)

    def draw(self, window):
        mute_icon = self.mute_icon if not self.is_muted else self.unmute_icon
        window.blit(mute_icon, (10, HEIGHT - mute_icon.get_height() - 10)) 

mute_button = MuteButton()

class Laser:
    def __init__(self, x, y, img):
        self.x, self.y = x, y 
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(0 <= self.y <= height)

    def collision(self, obj):
        return collide(obj, self)

class Ship:
    COOLDOWN = 15

    def __init__(self, x, y, health=100):
        self.x, self.y = x, y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            self.lasers.append(Laser(self.x, self.y, self.laser_img))
            self.cool_down_counter = 1

            LASER_SOUND.set_volume(0.1 if not mute_button.is_muted else 0.0)
            LASER_SOUND.play()

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10  
                self.lasers.remove(laser)

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x=WIDTH // 2 - PLAYER_SHIP.get_width() // 2, y=HEIGHT - PLAYER_SHIP.get_height() - 10, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SHIP
        self.laser_img = PLAYER_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        bar_width = self.ship_img.get_width()
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, bar_width, 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10,
                         bar_width * (1 - ((self.max_health - self.health) / self.max_health)), 10))

class Enemy(Ship):
    COLOR_MAP = {"red": (RED_SPACESHIP, RED_LASER),
                 "green": (GREEN_SPACESHIP, GREEN_LASER),
                 "blue": (BLUE_SPACESHIP, BLUE_LASER)}

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 18, self.y, self.laser_img)
            if 0 <= laser.y <= HEIGHT: 
                LASER_SOUND.set_volume(0.1 if not mute_button.is_muted else 0.0)
                LASER_SOUND.play()
            self.lasers.append(laser)
            self.cool_down_counter = 1

def collide(obj1, obj2):
    offset_x, offset_y = obj2.x - obj1.x, obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None

pygame.font.init()

async def main():
    run = False
    FPS = 60
    LEVEL, LIVES = 0, 5
    MAIN_FONT = pygame.font.Font('Assets/Font assets/SPACEMAN.TTF', 30)
    LOST_FONT = pygame.font.Font('Assets/Font assets/SPACEMAN.TTF', 30)
    ENEMIES = []
    WAVE_LEN, ENEMY_VEL, PLAYER_VEL, LASER_VEL = 5, 1, 5, 8
    LOST = False
    PLAYER = Player(300, 630)
    pygame.mixer.music.play(-1) 
    pygame.mixer.music.set_volume(0.1 if not mute_button.is_muted else 0.0)
    CLOCK = pygame.time.Clock()

    while not run:
        CLOCK.tick(FPS)
        WIN.blit(BACKGROUND, (0, 0))
        
        start_message = MAIN_FONT.render("Click to Start", True, (255, 255, 255))
        WIN.blit(start_message, (WIDTH // 2 - start_message.get_width() // 2, HEIGHT // 2 - start_message.get_height() // 2))
        
        PLAYER = Player(WIDTH // 2 - PLAYER_SHIP.get_width() // 2, HEIGHT - PLAYER_SHIP.get_height() - 30)
        PLAYER.draw(WIN)
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                run = True 

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 10 <= event.pos[0] <= 10 + mute_button.mute_icon.get_width() and \
                   HEIGHT - 10 - mute_button.mute_icon.get_height() <= event.pos[1] <= HEIGHT - 10:
                    mute_button.toggle_mute()
                else:
                    run = True 

        await asyncio.sleep(0)

    while run:
        CLOCK.tick(FPS)
        WIN.blit(BACKGROUND, (0, 0))
        mute_button.draw(WIN)
        lives_label = MAIN_FONT.render(f"Lives: {LIVES}", True, (255, 255, 255))
        level_label = MAIN_FONT.render(f"Level: {LEVEL}", True, (255, 255, 255))
        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        for enemy in ENEMIES:
            enemy.draw(WIN)
        PLAYER.draw(WIN)

        if LOST:
            lost_label = LOST_FONT.render("You Lost! Click to restart", True, (255, 255, 255))
            WIN.blit(lost_label, (WIDTH // 2 - lost_label.get_width() // 2, 350))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Reset the game state
                    LEVEL, LIVES = 0, 5
                    ENEMIES = []
                    WAVE_LEN, ENEMY_VEL, PLAYER_VEL, LASER_VEL = 5, 1, 5, 8
                    LOST = False
                    PLAYER = Player(WIDTH // 2 - PLAYER_SHIP.get_width() // 2, HEIGHT - PLAYER_SHIP.get_height() - 30)
                    PLAYER.draw(WIN)

        if LIVES <= 0 or PLAYER.health <= 0:
            LOST = True

        if len(ENEMIES) == 0:
            LEVEL += 1
            WAVE_LEN += 5
            ENEMIES.extend(Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                                random.choice(["red", "blue", "green"])) for _ in range(WAVE_LEN))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                PLAYER.shoot()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 10 <= event.pos[0] <= 10 + mute_button.mute_icon.get_width() and \
                HEIGHT - 10 - mute_button.mute_icon.get_height() <= event.pos[1] <= HEIGHT - 10:
                    mute_button.toggle_mute()
                    pygame.mixer.music.set_volume(0.1 if not mute_button.is_muted else 0.0)
                else:
                    PLAYER.shoot()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and PLAYER.x - PLAYER_VEL > 0:  # left
            PLAYER.x -= PLAYER_VEL
        if keys[pygame.K_d] and PLAYER.x + PLAYER_VEL + PLAYER.get_width() < WIDTH:  # right
            PLAYER.x += PLAYER_VEL
        if keys[pygame.K_w] and PLAYER.y - PLAYER_VEL > 0:  # up
            PLAYER.y -= PLAYER_VEL
        if keys[pygame.K_s] and PLAYER.y + PLAYER_VEL + PLAYER.get_height() + 15 < HEIGHT:  # down
            PLAYER.y += PLAYER_VEL

        enemies_to_remove = []

        for enemy in ENEMIES:
            if not LOST:
                enemy.move(ENEMY_VEL)
                enemy.move_lasers(LASER_VEL, PLAYER)

            if random.randrange(0, 2 * FPS) == 1 and not LOST:  
                enemy.shoot()

            if collide(enemy, PLAYER) and not LOST:
                PLAYER.health -= 10
                enemies_to_remove.append(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT and not LOST:
                LIVES -= 1
                enemies_to_remove.append(enemy)

        for enemy in enemies_to_remove:
            ENEMIES.remove(enemy)

        PLAYER.move_lasers(-LASER_VEL, ENEMIES)
        
        pygame.display.update()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())