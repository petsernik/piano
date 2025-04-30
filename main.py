import pygame
import numpy as np
from mingus.core import scales, notes

# Initialize Pygame
pygame.init()

# Display settings
WIDTH, HEIGHT = 800, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tonal Piano - C Major Scale")

# Audio settings
SAMPLE_RATE = 44100
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
# Allow polyphony: multiple simultaneous voices
pygame.mixer.set_num_channels(32)

class PianoKey:
    def __init__(self, midi, rect, color, in_scale):
        self.midi = midi
        self.rect = rect
        self.color = color
        self.in_scale = in_scale
        self.active = False

    def play(self, duration=1.0):
        # Generate harmonics
        freq = 440.0 * 2 ** ((self.midi - 69) / 12)
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        wave = (0.6 * np.sin(2 * np.pi * freq * t) +
                0.3 * np.sin(2 * np.pi * 2 * freq * t) +
                0.1 * np.sin(2 * np.pi * 3 * freq * t) +
                0.05 * np.sin(2 * np.pi * 4 * freq * t))
        # ADSR envelope
        attack, decay, sustain_level, release = 0.01, 0.1, 0.7, 0.2
        env = np.zeros_like(t)
        a, d, r = int(attack * SAMPLE_RATE), int(decay * SAMPLE_RATE), int(release * SAMPLE_RATE)
        s_start = a + d
        if a: env[:a] = np.linspace(0, 1, a)
        if d: env[a:s_start] = np.linspace(1, sustain_level, d)
        env[s_start:len(t)-r] = sustain_level
        if r: env[-r:] = np.linspace(sustain_level, 0, r)
        wave *= env
        # Mix down to 16-bit PCM
        audio = np.clip(wave * 32767, -32767, 32767).astype(np.int16)
        sound = pygame.mixer.Sound(buffer=audio.tobytes())
        # Play with slight fade-in to avoid clicks
        channel = pygame.mixer.find_channel(True)
        channel.play(sound, fade_ms=10)
        normalize_volumes()


def normalize_volumes():
    # Balance volume across active channels to prevent clipping
    busy = []
    for i in range(pygame.mixer.get_num_channels()):
        ch = pygame.mixer.Channel(i)
        if ch.get_sound():
            busy.append(ch)
    count = len(busy)
    if count > 0:
        vol = 1.0 / count
        for ch in busy:
            ch.set_volume(vol)


def create_piano_layout(scale_notes):
    keys = []
    white_w, white_h = 40, 160
    black_w, black_h = 24, 100

    white_x = 0
    last_white_x = 0
    for midi in range(48, 84):  # C3–B5
        name = notes.int_to_note(midi % 12)
        in_scale = name in scale_notes
        if '#' not in name:
            rect = pygame.Rect(white_x, HEIGHT - white_h, white_w, white_h)
            keys.append(PianoKey(midi, rect, (255,255,255), in_scale))
            last_white_x = white_x
            white_x += white_w
        else:
            bx = last_white_x + white_w - black_w // 2
            rect = pygame.Rect(bx, HEIGHT - white_h, black_w, black_h)
            keys.append(PianoKey(midi, rect, (0,0,0), in_scale))
    # White keys first
    keys.sort(key=lambda k: k.color == (0,0,0))
    return keys

# Setup scale constraints
current_scale = scales.Major("C").ascending()
scale_notes = [n[0] for n in current_scale]
piano_keys = create_piano_layout(scale_notes)

# Map keyboard to MIDI (three octaves)
key_map = {
    pygame.K_z:48, pygame.K_s:49, pygame.K_x:50, pygame.K_d:51,
    pygame.K_c:52, pygame.K_v:53, pygame.K_g:54, pygame.K_b:55,
    pygame.K_h:56, pygame.K_n:57, pygame.K_j:58, pygame.K_m:59,
    pygame.K_q:60, pygame.K_2:61, pygame.K_w:62, pygame.K_3:63,
    pygame.K_e:64, pygame.K_r:65, pygame.K_5:66, pygame.K_t:67,
    pygame.K_6:68, pygame.K_y:69, pygame.K_7:70, pygame.K_u:71,
    pygame.K_a:72, pygame.K_f:73, pygame.K_k:74, pygame.K_l:75,
    pygame.K_SEMICOLON:76, pygame.K_QUOTE:77, pygame.K_o:78,
    pygame.K_9:79, pygame.K_p:80, pygame.K_MINUS:81,
    pygame.K_LEFTBRACKET:82, pygame.K_EQUALS:83
}

midi_to_key = {key.midi:key for key in piano_keys}

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for key in reversed(piano_keys):
                if key.rect.collidepoint(event.pos): key.play(); key.active=True; break
        elif event.type == pygame.MOUSEBUTTONUP:
            for key in piano_keys: key.active=False
        elif event.type == pygame.KEYDOWN and event.key in key_map:
            key = midi_to_key.get(key_map[event.key])
            if key: key.play(); key.active=True
        elif event.type == pygame.KEYUP and event.key in key_map:
            key = midi_to_key.get(key_map[event.key])
            if key: key.active=False

    # Draw
    screen.fill((50,50,50))
    for key in piano_keys:
        base = key.color if key.in_scale else (100,100,100)
        if key.active:
            color = (255,200,0) if base==(255,255,255) else (200,150,0)
        else:
            color = base
        pygame.draw.rect(screen, color, key.rect)
        if key.color==(0,0,0) and key.in_scale:
            pygame.draw.rect(screen,(200,200,200),key.rect,1)
    pygame.display.flip()
pygame.quit()
