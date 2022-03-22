import pygame
from pygame import FULLSCREEN
import random
import time
import math
import copy

#window setup
import ctypes
user32 = ctypes.windll.user32
global scr_width
global scr_height
scr_width = user32.GetSystemMetrics(0)
scr_height = user32.GetSystemMetrics(1)
window = pygame.display.set_mode((scr_width,scr_height),FULLSCREEN)
pygame.display.set_caption("LARCH")
pygame.font.init()
from pygame.locals import *
pygame.init()


#Objects
class Board:
    def __init__(self):
        #dimensions
        self.height = 900 
        self.width = 1915
        self.coord = [scr_width//2-self.width//2,scr_height//2-self.height//2]
        self.rect = pygame.Rect(self.coord[0], self.coord[1], self.width, self.height)

        #gameplay
        self.score = [0,0]
        self.round = 1
        self.rounddelay = 300
        self.NextRound = False
        self.projectiles = []
        self.explosions = []
        self.ships = []
        self.particles = []

        #sound
        self.explod = pygame.mixer.Sound("sounds\explod.wav")
        self.ambience = pygame.mixer.Sound("sounds\\ambience.wav")
    
    def Show(self):
        pygame.draw.rect(window,(215,218,193),self.rect)

        #Round number
        SubFont = pygame.font.SysFont('', 100)
        Text = SubFont.render("RND "+str(self.round), False, (247,216,148))
        window.blit(Text,(10,10))

        #Score
        Text = SubFont.render("SCR "+str(self.score[0])+":"+str(self.score[1]), False, (247,216,148))
        window.blit(Text,(scr_width-270,10))

        #NextRound 
        if self.NextRound:
            details = (self.coord[0], self.coord[1], self.rounddelay, 15)
            pygame.draw.rect(window,(43,173,206),details)

        #signature
        SigFont = pygame.font.SysFont('', 25)
        Text = SigFont.render(("BY RICHARD BURGIN"), False, (247,216,148))
        window.blit(Text,(30,scr_height-50))

        #ambience
        if not pygame.mixer.get_busy():
            pygame.mixer.Sound.play(self.ambience)

    def Handling(self, ROUND):
        for i in self.ships:
            if i.health == 0 and self.NextRound == False:
                B.explosions.append(Explosion(i.coord, 1))
                pygame.mixer.Sound.play(self.explod)
                self.NextRound = True
                if i.player == 1:
                    self.score[1] += 1
                else:
                    self.score[0] += 1

        if self.NextRound:
            if self.rounddelay > 0:
                self.rounddelay -= 1
            else:
                self.round += 1
                ROUND = False
                
        return ROUND

    def Title(self):
        TitleFont = pygame.font.SysFont('', 500)
        Text = TitleFont.render(("LARCH"), False, (247,216,148))
        window.blit(Text,(scr_width//2-600,scr_height//2-125))

    def Select(self, player, pointer, SET):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                pass
        change = False
        if player == 1:
            if keys[pygame.K_w]:
                pointer -= 1
                change = True
            if keys[pygame.K_s]:
                pointer += 1
                change = True
            if keys[pygame.K_SPACE]:
                if SET:
                    SET = False
                else:
                    SET = True
                change = True

        else:
            if keys[pygame.K_UP]:
                pointer -= 1
                change = True
            if keys[pygame.K_DOWN]:
                pointer += 1
                change = True
            if keys[pygame.K_KP_ENTER]:
                if SET:
                    SET = False
                else:
                    SET = True
                change = True

        return SET, pointer, change

    def Hangar(self, player, delay, pointer, SET):
        ShipSet = [Light_Ship(player),Medium_Ship(player),Heavy_Ship(player)]

        #delay
        if delay > 0:
            delay -= 1

        #input
        change = False
        if delay == 0:
            SET, pointer, change = B.Select(player , pointer, SET)
        if pointer == len(ShipSet):
            pointer = 0
        elif pointer == -1:
            pointer = len(ShipSet) - 1
        #gen
        if change:
            delay = 25
            B.ships[player-1] = ShipSet[pointer]

        return SET, delay, pointer

    def SetIndicators(self, SET):
        for i in range(0,2):
            if SET[i]:
                if i == 0:
                    details = self.coord[0], self.coord[1], self.width//2, self.height
                else:
                    details = self.coord[0]+self.width//2, self.coord[1], self.width//2, self.height
                pygame.draw.rect(window,(200,203,178),details)

class Entity:
    def __init__(self,X,Y):
        #images
        self.image = self.neutral
        self.blitimage = self.image

        #gameplay
        self.coord = [X,Y]
        self.blit = [0,0]
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect = pygame.Rect(self.coord[0],self.coord[1],self.width,self.height)

        #suvat
        self.F = [0,0]
        self.u = [0,0]
        self.a = [0,0]
        self.s = [0,0]

    def Calculate(self):
        self.BoundaryCheck()
        Resultant_F = []
        #find resultant force in axis (F=ma)
        Resultant_F.append(self.F[0]) 
        Resultant_F.append(self.F[1])

        for i in range (0,2):
            #find acceleration on axis
            self.a[i] = 0
            if Resultant_F[i] != 0:
                self.a[i] =  Resultant_F[i] / self.m

            #find displacement on axis (s = ut- 1/2 at^2)
            self.s[i] = self.u[i] - 0.5*self.a[i]

        #displace
        self.coord[0] -= self.s[0]
        self.coord[1] += self.s[1]
        
    def Reset(self):
        #find velocity used in next Calculate (v = u + at)
        for i in range (0,2):
            self.u[i] = self.u[i] + self.a[i]
            self.u[i] *= 0.996

            #reset values
            self.F[i] = 0
        self.image = self.neutral
   
class Ship(Entity):
    def __init__(self, player):
        #gameplay
        self.player = player
        self.heat = 0
        self.strength = 0
        self.delay = 0
        self.shield = True
        self.deaddelay = 0

        #sounds
        self.pew = pygame.mixer.Sound("sounds\\bit.wav")
        self.hit = pygame.mixer.Sound("sounds\hit.wav")
        self.brek = pygame.mixer.Sound("sounds\shield.wav")
        self.regen = pygame.mixer.Sound("sounds\\regen.wav")

        #inherit
        if self.player == 1:
            X = 200
        else:
            X = scr_width - 200
        Y = scr_height//2
        super().__init__(X,Y)

    def Input(self):
        self.strength = 0
        if self.delay > 0:
            self.delay -= 1

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                pass
        if self.player == 1:
            if keys[pygame.K_w]:
                self.Active()
            if keys[pygame.K_a]:
                self.deg += self.turnrate
            if keys[pygame.K_d]:
                self.deg -= self.turnrate
            if keys[pygame.K_SPACE]:
                if self.delay == 0 and self.heat < self.overheat:
                    pygame.mixer.Sound.play(self.pew)
                    angle = copy.deepcopy(self.deg) + random.randint(-self.spray, self.spray)
                    B.projectiles.append(Projectile(copy.deepcopy(self.coord[0]),copy.deepcopy(self.coord[1]),copy.deepcopy(self.u), angle))
                    self.delay = self.gunrate
                    self.heat += 50
        else:
            if keys[pygame.K_UP]:
                self.Active()
            if keys[pygame.K_LEFT]:
                self.deg += self.turnrate
            if keys[pygame.K_RIGHT]:
                self.deg -= self.turnrate
            if keys[pygame.K_KP_ENTER]:
                if self.delay == 0 and self.heat < self.overheat:
                    pygame.mixer.Sound.play(self.pew)
                    angle = copy.deepcopy(self.deg) + random.randint(-self.spray, self.spray)
                    B.projectiles.append(Projectile(copy.deepcopy(self.coord[0]),copy.deepcopy(self.coord[1]),copy.deepcopy(self.u), angle))
                    self.delay = self.gunrate
                    self.heat += 50

    def Show(self):
        #shield
        if self.shield:
            pygame.draw.circle(window, (43,173,206), (int(self.coord[0]),int(self.coord[1])), 45, 3)

        elif self.shielddelay > 0:
            self.shielddelay -= 1
            details = (self.coord[0]-self.shielddelay//2, self.coord[1]-50, self.shielddelay, 3)
            pygame.draw.rect(window,(43,173,206),details)

        #image
        self.width = self.blitimage.get_width()
        self.height = self.blitimage.get_height()
        self.blitimage = pygame.transform.rotate(self.image, self.deg)
        self.blit = [self.coord[0] - self.width/2,self.coord[1] - self.height/2]
        window.blit(self.blitimage,(self.blit[0] , self.blit[1]))
        self.rect = pygame.Rect(self.blit[0],self.blit[1],self.width,self.height)

        #heat meter
        if self.heat > 0:
            self.heat -= self.cool
        if self.heat > 0:
            details = (self.coord[0]+40, self.coord[1]-25, 3, self.heat/4)
            pygame.draw.rect(window,(255,self.overheat//4 + 50 - self.heat//4, self.overheat//4 + 50 - self.heat//4),details)

        #health
        for i in range(0,self.health):
            pygame.draw.circle(window, (33,105,91), (int(self.coord[0])-40+ (i*15),int(self.coord[1])+25+i*10), 3, 0)

    def BoundaryCheck(self):
        if (self.blit[0] < B.coord[0]) or (self.blit[0]+self.width > B.coord[0]+B.width):
            self.u[0] = -self.u[0]
            self.a[0] = -self.a[0]
            if self.shield == False and not self.shielddelay > 0 and self.health > 0:
                self.shield = True
                pygame.mixer.Sound.play(self.regen)

        if (self.blit[1] < B.coord[1]) or (self.blit[1]+self.height > B.coord[1]+B.height):
            self.u[1] = -self.u[1]
            self.a[1] = -self.a[1]
            if self.shield == False and not self.shielddelay > 0 and self.health > 0:
                self.shield = True
                pygame.mixer.Sound.play(self.regen)

    def Active(self):
        self.strength = self.thrust

        #pythagoras
        radians = math.radians(self.deg)
        opp = self.strength * math.sin(radians)
        adj = self.strength * math.cos(radians)
        self.F[0] = -opp
        self.F[1] = adj

    def Dead(self):
        self.image = self.dead
        x = random.randint(-20,20) + self.coord[0]
        y = random.randint(-20,20) + self.coord[1]
        if self.deaddelay > 0:
            self.deaddelay -= 1
        else:
            B.explosions.append(Explosion([x,y], 0))
            self.deaddelay = 10

class Heavy_Ship(Ship):
    def __init__(self, player):
        #images
        if player == 1:
            self.deg = 90
            self.neutral = pygame.image.load("images\ship2_neutral#1.png")
        else:
            self.deg = -90
            self.neutral = pygame.image.load("images\ship2_neutral#2.png")
        self.dead = pygame.image.load("images\ship2_dead.png")

        #differentaition
        self.health = 4
        self.thrust = 1
        self.turnrate = 1
        self.overheat = 500
        self.cool = 1.5
        self.m = 50
        self.gunrate = 5
        self.spray = 5

        #instanciate
        super().__init__(player)

class Medium_Ship(Ship):
    def __init__(self, player):
        #images
        if player == 1:
            self.deg = 90
            self.neutral = pygame.image.load("images\ship_neutral#1.png")
        else:
            self.deg = -90
            self.neutral = pygame.image.load("images\ship_neutral#2.png")
        self.dead = pygame.image.load("images\ship_dead.png")

        #differentaition
        self.health = 3
        self.thrust = 0.5
        self.turnrate = 2
        self.overheat = 200
        self.cool = 1
        self.m = 10
        self.gunrate = 10
        self.spray = 1

        #instanciate
        super().__init__(player)

class Light_Ship(Ship):
    def __init__(self, player):
        #images
        if player == 1:
            self.deg = 90
            self.neutral = pygame.image.load("images\ship3_neutral#1.png")
        else:
            self.deg = -90
            self.neutral = pygame.image.load("images\ship3_neutral#2.png")
        self.dead = pygame.image.load("images\ship3_dead.png")

        #differentaition
        self.health = 1
        self.thrust = 0.8
        self.turnrate = 2.5
        self.overheat = 100
        self.cool = 0.5
        self.m = 5
        self.gunrate = 15
        self.spray = 0

        #instanciate
        super().__init__(player)

class Projectile(Entity):
    def __init__(self,X,Y,u,deg):
        #images
        self.neutral = pygame.image.load("images\projectile.png")

        super().__init__(X,Y)
        self.u = u
        self.deg = deg
        self.m = 5
        self.Launch()
        self.bounce = 1
        self.delay = 10

    def Show(self): 
        #delete slow projectiles
        if self.delay > 0:
            self.delay -= 1
        elif self.u[0] < .5 and self.u[1] < .5 and self.u[0] > -.5 and self.u[1] > -.5:
            B.explosions.append(Explosion(self.coord, 0))
            self.Terminate()
        

        self.rect = pygame.Rect(self.coord[0],self.coord[1],self.width,self.height)
        window.blit(self.blitimage, (self.coord[0],self.coord[1]))

    def BoundaryCheck(self):
        if (self.coord[0] < B.coord[0]) or (self.coord[0]+self.width > B.coord[0]+B.width):
            if self.bounce <= 0:
                B.explosions.append(Explosion(self.coord, 0))
                self.Terminate()
            else:
                self.u[0] = -self.u[0]
                self.a[0] = -self.a[0]
                self.bounce -= 1


        if (self.coord[1] < B.coord[1]) or (self.coord[1]+self.height > B.coord[1]+B.height):
            if self.bounce <= 0:
                B.explosions.append(Explosion(self.coord, 0))
                self.Terminate()
            else:
                self.u[1] = -self.u[1]
                self.a[1] = -self.a[1]
                self.bounce -= 1

    def Launch(self):
        self.strength = 50
        #self.image = self.active

        #pythagoras
        radians = math.radians(self.deg)
        opp = self.strength * math.sin(radians)
        adj = self.strength * math.cos(radians)
        self.F[0] = -opp
        self.F[1] = adj

    def Impact(self):
        for S in B.ships:
            if self.rect.colliderect(S.rect) and self.delay <= 0:
                if S.shield:
                    pygame.mixer.Sound.play(S.brek)
                    S.shield = False
                    S.shielddelay = 200
                else:
                    pygame.mixer.Sound.play(S.hit)
                    S.health -= 1
                for i in range(0,2):
                    #finds momentum
                    self.p = self.m * self.u[i]
                    S.P = S.m * S.u[i]
                    #combines momentum
                    totalp = self.p + S.P
                    #finds u
                    S.u[i] = totalp / S.m
                B.explosions.append(Explosion(self.coord, 0))
                self.Terminate()

    def Terminate(self):
        try:
            B.projectiles.remove(self)
        except:
            ValueError

class Explosion:
    def __init__(self, coord, big):
        #images
        self.cycle = []
        for i in range(1,7):
            self.cycle.append(pygame.image.load("images\\"+(big * "big")+"explosion#"+str(i)+".png"))
        #behaviour
        self.index = 0
        self.image = self.cycle[self.index]
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.coord = [coord[0]-self.width/2, coord[1]-self.height/2]
        self.delay = 5

        #particle effects
        for p in range(0,25):
                B.particles.append(Particles(copy.deepcopy(self.coord)))

    def Show(self):
        #show
        self.image = self.cycle[self.index]
        window.blit(self.image, (self.coord[0],self.coord[1]))

        #time
        if self.delay < 0:
            self.index += 1
            self.delay = 5
        else:
            self.delay -= 1

        #terminate
        if self.index > 5:
            B.explosions.remove(self)

class Particles:
    def __init__(self, coord):
        self.coord = coord
        self.deg = random.randint(0, 360)
        self.vel = random.randint(1,5)

    def Move(self):
        rad = math.radians(self.deg)
        opp = self.vel * math.sin(rad)
        adj = self.vel * math.cos(rad)

        self.coord[0] += opp
        self.coord[1] += adj

        pygame.draw.circle(window, (51,66,77), (int(self.coord[0]), int(self.coord[1])), int(self.vel), 0)

        #entropy
        if random.choice([True,False]):
            self.deg += random.randint(-10,10)
        self.vel -= .05
        if self.vel <= 0:
            B.particles.remove(self)

#functions
def TitleScreen():
    B.ships = []
    B.ships.append(Medium_Ship(1))
    B.ships.append(Medium_Ship(2))
    delay = [0,0]
    pointer = [1,1]
    SET = [False, False]
    while not SET[0] or not SET[1]:
        pygame.time.delay(1)
        window.fill((32,31,56))

        for i in range(0,2):
            SET[i], delay[i], pointer[i] = B.Hangar((i+1),delay[i], pointer[i], SET[i])

        #show
        B.Show()
        B.SetIndicators(SET)
        for S in B.ships:
            S.Show()
        B.Title()

        pygame.display.update()

    countdown = 500
    Timer = True
    while Timer:
        pygame.time.delay(1)
        window.fill((32,31,56))

        #timer
        if countdown < 0:
            Timer = False
        else:
            countdown -= 2

        #show
        B.Show()
        for S in B.ships:
            S.Show()
        B.Title()
        details = scr_width//2-countdown, scr_height//2+150, countdown*2, 25
        pygame.draw.rect(window,(43,173,206),details)

        pygame.display.update()     


if __name__ == '__main__':
    B = Board()
    RUN = True
    while RUN:
        B.ships = []
        B.explosions = []
        B.projectiles = []
        B.rounddelay = 300
        B.NextRound = False
        TitleScreen()
        ROUND = True
        while ROUND:
            pygame.time.delay(1)
            window.fill((32,31,56))
            for S in B.ships:
                if S.health > 0:
                    S.Input()
                else:
                    S.Dead()
            B.Show()

            for i in B.projectiles:
                i.Calculate()
                i.Impact()
            for S in B.ships:
                S.Calculate()

            for i in B.particles:
                i.Move()
            for i in B.projectiles:
                i.Show()
            for S in B.ships:
                S.Show()
            for i in B.explosions:
                i.Show()

            for i in B.projectiles:
                i.Reset()
            for S in B.ships:
                S.Reset()

            
            ROUND = B.Handling(ROUND)
            pygame.display.update()
