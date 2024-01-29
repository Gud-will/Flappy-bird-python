import pygame, random, time
from pygame.locals import *
import numpy as np
from time import sleep

#VARIABLES
SCREEN_WIDHT = 400
SCREEN_HEIGHT = 600
SPEED = 20
GRAVITY = 2.5
GAME_SPEED = 15

GROUND_WIDHT = 2 * SCREEN_WIDHT
GROUND_HEIGHT= 100

PIPE_WIDHT = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()


class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.images =  [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]

        self.speed = SPEED

        self.current_image = 0
        self.image = pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDHT / 6
        self.rect[1] = SCREEN_HEIGHT / 2

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += GRAVITY

        #UPDATE HEIGHT
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]




class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self. image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDHT, PIPE_HEIGHT))


        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            print(self.rect[3],ysize,- (self.rect[3] - ysize))
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize


        self.mask = pygame.mask.from_surface(self.image)


    def update(self):
        self.rect[0] -= GAME_SPEED

        

class Ground(pygame.sprite.Sprite):
    
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDHT, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT
    def update(self):
        self.rect[0] -= GAME_SPEED

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted


class FlappyGameAi():
    def __init__(self) -> None:
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen= pygame.display.set_mode((SCREEN_WIDHT, SCREEN_HEIGHT))
        pygame.display.set_caption('Flappy Bird')
        self.BACKGROUND = pygame.image.load('assets/sprites/background-day.png')
        self.BACKGROUND = pygame.transform.scale(self.BACKGROUND, (SCREEN_WIDHT, SCREEN_HEIGHT))
        self.BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()
        self.reset()

    def reset(self):
        self.score=0
        self.crossed=False
        self.bird_group = pygame.sprite.Group()
        self.bird = Bird()
        self.bird_group.add(self.bird)
        self.ground_group = pygame.sprite.Group()
        for i in range (2):
            ground = Ground(GROUND_WIDHT * i)
            self.ground_group.add(ground)

        self.pipe_group = pygame.sprite.Group()
        for i in range (2):
            pipes = get_random_pipes(SCREEN_WIDHT * i + 800)
            self.pipe_group.add(pipes[0])
            self.pipe_group.add(pipes[1])

    def play_step(self,action):
        if np.array_equal(action,[1,0]):
            self.bird.bump()
            # pygame.mixer.music.load(wing)
            # pygame.mixer.music.play()
        reward=0
        game_over=False
        self.screen.blit(self.BACKGROUND, (0, 0))
        # SCREEN_WIDHT / 6
        # print(self.bird_group.sprites()[0].rect[0],)
        # self.crossed=False
        if (self.bird_group.sprites()[0].rect[1])<0:
            reward=-50
            self.reset()
            game_over=True
        elif (self.pipe_group.sprites()[0].rect[0])+PIPE_WIDHT<(SCREEN_WIDHT / 6) and not self.crossed:
            reward=10
            self.score+=1
            self.crossed=not self.crossed
            print(self.score,self.crossed)
        elif is_off_screen(self.ground_group.sprites()[0]):
            self.ground_group.remove(self.ground_group.sprites()[0])
            new_ground = Ground(GROUND_WIDHT - 20)
            self.ground_group.add(new_ground)
            reward=10
        elif is_off_screen(self.pipe_group.sprites()[0]):
            self.crossed=not self.crossed
            self.pipe_group.remove(self.pipe_group.sprites()[0])
            self.pipe_group.remove(self.pipe_group.sprites()[0])
            pipes = get_random_pipes(SCREEN_WIDHT * 2)
            self.pipe_group.add(pipes[0])
            self.pipe_group.add(pipes[1])

        self.bird_group.update()
        self.ground_group.update()
        self.pipe_group.update()

        self.bird_group.draw(self.screen)
        self.pipe_group.draw(self.screen)
        self.ground_group.draw(self.screen)

        pygame.display.update()
        self.clock.tick(10)
        if (pygame.sprite.groupcollide(self.bird_group,self.ground_group, False, False, pygame.sprite.collide_mask) or
                pygame.sprite.groupcollide(self.bird_group, self.pipe_group, False, False, pygame.sprite.collide_mask)):
            pygame.mixer.music.load(hit)
            pygame.mixer.music.play()
            time.sleep(1)
            reward=-10
            self.reset()
            game_over=True
        
        return reward, game_over, self.score



clock = pygame.time.Clock()

# begin = True

# while begin:

#     clock.tick(15)

#     for event in pygame.event.get():
#         if event.type == QUIT:
#             pygame.quit()
#         if event.type == KEYDOWN:
#             if event.key == K_SPACE or event.key == K_UP:
#                 bird.bump()
#                 pygame.mixer.music.load(wing)
#                 pygame.mixer.music.play()
#                 begin = False

#     screen.blit(BACKGROUND, (0, 0))
#     screen.blit(BEGIN_IMAGE, (120, 150))

#     if is_off_screen(ground_group.sprites()[0]):
#         ground_group.remove(ground_group.sprites()[0])

#         new_ground = Ground(GROUND_WIDHT - 20)
#         ground_group.add(new_ground)

#     bird.begin()
#     ground_group.update()

#     bird_group.draw(screen)
#     ground_group.draw(screen)

#     pygame.display.update()

# g=FlappyGameAi()
# while True:

#     clock.tick(15)
#     for event in pygame.event.get():
#         if event.type == QUIT:
#             pygame.quit()
#         if event.type == KEYDOWN:
#             if event.key == K_SPACE or event.key == K_UP:
#                 _,game,_=g.play_step([1,0])
#                 if game==True:
#                     break
#                 pygame.mixer.music.load(wing)
#                 pygame.mixer.music.play()
#     _,game,_=g.play_step([0,1])

#     # if is_off_screen(ground_group.sprites()[0]):
#     #     ground_group.remove(ground_group.sprites()[0])

#     #     new_ground = Ground(GROUND_WIDHT - 20)
#     #     ground_group.add(new_ground)

#     # if is_off_screen(pipe_group.sprites()[0]):
#     #     pipe_group.remove(pipe_group.sprites()[0])
#     #     pipe_group.remove(pipe_group.sprites()[0])

#     #     pipes = get_random_pipes(SCREEN_WIDHT * 2)

#     #     pipe_group.add(pipes[0])
#     #     pipe_group.add(pipes[1])

#     # bird_group.update()
#     # ground_group.update()
#     # pipe_group.update()

#     # bird_group.draw(screen)
#     # pipe_group.draw(screen)
#     # ground_group.draw(screen)

#     # pygame.display.update()

#     # if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
#     #         pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
#     #     pygame.mixer.music.load(hit)
#     #     pygame.mixer.music.play()
#     #     time.sleep(1)
#     #     break

