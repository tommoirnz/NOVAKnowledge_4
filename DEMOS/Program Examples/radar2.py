import pygame
import math
import random
import sys
import numpy as np

# ------------------------------------------------
# AUDIO INITIALIZATION
# ------------------------------------------------

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

print("Mixer:", pygame.mixer.get_init())

# ------------------------------------------------
# SCREEN
# ------------------------------------------------

WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Radar System Simulation")

phosphor_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# ------------------------------------------------
# COLORS
# ------------------------------------------------

BLACK = (0,0,0)
GREEN = (0,255,0)
DARK_GREEN = (0,80,0)
RED = (255,60,60)
CYAN = (0,255,255)
YELLOW = (255,255,0)
ORANGE = (255,165,0)

# ------------------------------------------------
# RADAR PARAMETERS
# ------------------------------------------------

CENTER_X = WIDTH//2
CENTER_Y = HEIGHT//2

MAX_RADIUS = 340
NUM_RINGS = 5
SWEEP_SPEED = 1.5

# ------------------------------------------------
# FONT
# ------------------------------------------------

font_small = pygame.font.SysFont("monospace",13)

# ------------------------------------------------
# SOUND SYSTEM
# ------------------------------------------------

SAMPLE_RATE = 44100

def make_sound_array(samples):

    samples = np.clip(samples,-1,1)

    int_samples = (samples*32767).astype(np.int16)

    stereo = np.column_stack((int_samples,int_samples))

    return pygame.sndarray.make_sound(stereo)

def generate_ping():

    duration=0.3
    freq=900

    t=np.linspace(0,duration,int(SAMPLE_RATE*duration),endpoint=False)

    env=np.exp(-t*10)

    wave=np.sin(2*np.pi*freq*t)*env

    return make_sound_array(wave.astype(np.float32))

def generate_motor():

    duration=2

    t=np.linspace(0,duration,int(SAMPLE_RATE*duration),endpoint=False)

    wave=0.05*np.sin(2*np.pi*40*t)
    wave+=0.02*np.sin(2*np.pi*80*t)

    mod=0.9+0.1*np.sin(2*np.pi*0.5*t)

    wave*=mod

    return make_sound_array(wave.astype(np.float32))

def generate_static():

    duration=0.05

    samples=int(SAMPLE_RATE*duration)

    noise=np.random.uniform(-1,1,samples)

    env=np.exp(-np.linspace(0,duration,samples)*50)

    wave=noise*env*0.2

    return make_sound_array(wave.astype(np.float32))

print("Generating sounds...")

ping_sound=generate_ping()
motor_sound=generate_motor()
static_sound=generate_static()

motor_channel=pygame.mixer.Channel(0)
ping_channel=pygame.mixer.Channel(1)

motor_channel.play(motor_sound,loops=-1)

# ------------------------------------------------
# TARGET CLASS
# ------------------------------------------------

class Target:

    def __init__(self):
        self.reset()

    def reset(self):

        angle=random.uniform(0,2*math.pi)
        dist=random.uniform(MAX_RADIUS*0.2,MAX_RADIUS*0.9)

        self.x=CENTER_X+dist*math.cos(angle)
        self.y=CENTER_Y+dist*math.sin(angle)

        self.vx=random.uniform(-0.3,0.3)
        self.vy=random.uniform(-0.3,0.3)

        self.size=random.randint(3,5)

        self.label=f"T{random.randint(1,99)}"

        self.blip_timer=0

        self.color=random.choice([GREEN,CYAN,YELLOW,ORANGE])

    def update(self):

        self.x+=self.vx
        self.y+=self.vy

        dx=self.x-CENTER_X
        dy=self.y-CENTER_Y

        dist=math.sqrt(dx*dx+dy*dy)

        if dist>MAX_RADIUS*0.95:

            self.vx*=-1
            self.vy*=-1

        if self.blip_timer>0:
            self.blip_timer-=1

    def get_angle(self):

        dx=self.x-CENTER_X
        dy=self.y-CENTER_Y

        return math.degrees(math.atan2(dy,dx))%360

# ------------------------------------------------
# TARGETS
# ------------------------------------------------

targets=[Target() for _ in range(8)]

# ------------------------------------------------
# MAIN LOOP
# ------------------------------------------------

clock=pygame.time.Clock()

sweep_angle=0

running=True

print("Radar running...")

while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type==pygame.QUIT:
            running=False

        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                running=False

    # phosphor fade
    fade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    fade.fill((0,0,0,25))
    phosphor_surface.blit(fade,(0,0))

    # radar rings
    for i in range(1,NUM_RINGS+1):

        r=int(MAX_RADIUS*i/NUM_RINGS)

        pygame.draw.circle(
            phosphor_surface,
            (0,80,0,120),
            (CENTER_X,CENTER_Y),
            r,
            1
        )

    # sweep beam glow
    for i in range(18):

        ang=sweep_angle-i*0.8

        rad=math.radians(ang)

        ex=CENTER_X+MAX_RADIUS*math.cos(rad)
        ey=CENTER_Y+MAX_RADIUS*math.sin(rad)

        alpha=max(30,255-i*15)

        pygame.draw.line(
            phosphor_surface,
            (0,alpha,0),
            (CENTER_X,CENTER_Y),
            (int(ex),int(ey)),
            2
        )

    # targets
    for t in targets:

        t.update()

        diff=(sweep_angle-t.get_angle())%360

        if diff<SWEEP_SPEED*2:

            if t.blip_timer==0:
                ping_channel.play(ping_sound)

            t.blip_timer=120

        if t.blip_timer>0:

            # glow effect
            for g in range(4):

                pygame.draw.circle(
                    phosphor_surface,
                    (0,255,0,60-g*15),
                    (int(t.x),int(t.y)),
                    t.size+g
                )

            pygame.draw.circle(
                phosphor_surface,
                (0,255,0,255),
                (int(t.x),int(t.y)),
                t.size
            )

            lbl=font_small.render(t.label,True,(0,255,0))

            phosphor_surface.blit(lbl,(int(t.x)+6,int(t.y)))

    # draw to screen
    screen.fill(BLACK)
    screen.blit(phosphor_surface,(0,0))

    pygame.display.flip()

    sweep_angle=(sweep_angle+SWEEP_SPEED)%360

pygame.quit()
sys.exit()