import pygame
import sys
import math
import struct

# ═══════════════════════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.joystick.init()

SW, SH = 1920, 1080

# Logical canvas – all game code draws here at the design resolution
screen   = pygame.Surface((SW, SH))

# Fullscreen display – the real window
_display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
_DSP_W, _DSP_H = _display.get_size()
pygame.display.set_caption("Grid Dodge")
clock  = pygame.time.Clock()
FPS    = 60

def _present():
    """Scale the logical canvas to the display, letterboxed, then flip."""
    scale = min(_DSP_W / SW, _DSP_H / SH)
    w, h  = int(SW * scale), int(SH * scale)
    _display.fill((0, 0, 0))
    _display.blit(pygame.transform.smoothscale(screen, (w, h)),
                  ((_DSP_W - w) // 2, (_DSP_H - h) // 2))
    pygame.display.flip()

# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════════════════════
BG        = ( 12,   9,  22)
C_SAFE    = ( 32,  26,  55)
C_SAFE_GRN= ( 30,  90,  50)
C_WARN      = (195, 138,   8)
C_FAKE_WARN = (  0, 200, 220)
C_HIT       = (188,  34,  34)
C_BORDER  = ( 68,  56, 108)
C_PLR     = (110, 225, 255)
C_PLR_HIT = (255,  85,  85)
C_PLR_DGD = ( 55, 205, 100)
WHITE     = (255, 255, 255)
GRAY      = (130, 130, 148)
DK_GRAY   = ( 55,  50,  75)
PURPLE    = (215, 168, 255)
TEAL      = ( 70, 220, 200)
GREEN     = ( 70, 210, 115)
RED       = (225,  72,  72)
GOLD      = (255, 205,  50)
ORANGE    = (255, 145,  40)

# ═══════════════════════════════════════════════════════════════════════════
#  GRID LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
CELL = 124
GAP  =   7
GW   = CELL * 3 + GAP * 2
GH   = CELL * 3 + GAP * 2
GX   = (SW - GW) // 2
GY   = (SH - GH) // 2 + 22

def cell_rect(r, c):
    """Return the pygame.Rect for grid cell (row r, column c)."""
    return pygame.Rect(GX + c * (CELL + GAP), GY + r * (CELL + GAP), CELL, CELL)

# ═══════════════════════════════════════════════════════════════════════════
#  SQUARE STATES  (imported from level_helpers so level files share them)
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import SAFE, WARN, ATCK, FAKE_WARN
import level_megalovania
import level_bigshot
import level_undyne
import level_histheme
import level_blackknife
import level_deathbyglamour

# ═══════════════════════════════════════════════════════════════════════════
#  CONTROLS  (DDR pad mapped to keyboard + joystick)
# ═══════════════════════════════════════════════════════════════════════════
# Keys map directly to a fixed grid cell; releasing snaps back to center.
#   U   O   →   (0,0) (0,2)
#   J   L   →   (1,0) (1,2)
#   M , .   →   (2,0) (2,1) (2,2)
KEY_POS = {
    pygame.K_u: (0, 0),                             pygame.K_o: (0, 2),
    pygame.K_j: (1, 0),                             pygame.K_l: (1, 2),
    pygame.K_m: (2, 0),  pygame.K_COMMA: (2, 1),   pygame.K_PERIOD: (2, 2),
}
CENTER = (1, 1)

# ── Joystick setup ───────────────────────────────────────────────────────────
_joysticks = []
for _i in range(pygame.joystick.get_count()):
    _j = pygame.joystick.Joystick(_i)
    _j.init()
    _joysticks.append(_j)
    print(f"[JOY] Found: {_j.get_name()}")

# Hat → grid cell.  SDL hat: X -1=left 1=right, Y -1=down 1=up
HAT_POS = {
    (-1,  1): (0, 0),  (-1,  0): (1, 0),  (-1, -1): (2, 0),
    ( 0,  1): (0, 1),  ( 0,  0): CENTER,  ( 0, -1): (2, 1),
    ( 1,  1): (0, 2),  ( 1,  0): (1, 2),  ( 1, -1): (2, 2),
}

# Button → grid cell (DDR pad read as PlayStation controller)
BTN_POS = {
    4:  (0, 1),  13: (0, 0),  14: (0, 2),
    7:  (1, 0),   5: (1, 2),
    15: (2, 0),   6: (2, 1),  12: (2, 2),
}

_joy_axes    = [0.0, 0.0]   # [x, y]
_AX_DEAD     = 0.5

def _axis_zone_from_values():
    x, y = _joy_axes
    row = 1 if abs(y) < _AX_DEAD else (0 if y < 0 else 2)
    col = 1 if abs(x) < _AX_DEAD else (0 if x < 0 else 2)
    return row, col

def _axes_to_pos():
    row, col = _axis_zone_from_values()
    return CENTER if (row == 1 and col == 1) else (row, col)

# ═══════════════════════════════════════════════════════════════════════════
#  FONTS  (PixelOperator TTF, fallback to pygame default)
# ═══════════════════════════════════════════════════════════════════════════
import os as _os
_FONT_REG  = _os.path.join("pixel_operator", "PixelOperator.ttf")
_FONT_BOLD = _os.path.join("pixel_operator", "PixelOperator-Bold.ttf")

def _font(size, bold=False):
    path = _FONT_BOLD if bold else _FONT_REG
    if _os.path.isfile(path):
        return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)

F_HUGE  = _font(96, True)
F_GRADE = _font(148, True)
F_BIG   = _font(64, True)
F_MED   = _font(44, True)
F_SM    = _font(30)
F_XS    = _font(22)

# ═══════════════════════════════════════════════════════════════════════════
#  PLAYER SPRITE  (heart.png, with circle fallback if file is missing)
# ═══════════════════════════════════════════════════════════════════════════
_HEART_PX = CELL - 28   # pixel size the heart is scaled to

def _make_tinted(base_surf, tint_rgb):
    """Return a copy of base_surf with every pixel multiplied by tint_rgb."""
    img = base_surf.copy()
    img.fill(tint_rgb, special_flags=pygame.BLEND_MULT)
    return img

try:
    _raw = pygame.image.load("heart.png").convert_alpha()
    HEART_BASE = pygame.transform.smoothscale(_raw, (_HEART_PX, _HEART_PX))
    HEART_HIT  = _make_tinted(HEART_BASE, (255,  80,  80))   # red flash
    HEART_DGD  = _make_tinted(HEART_BASE, ( 80, 255, 130))   # green dodge
    HEART_LOADED = True
except (pygame.error, FileNotFoundError):
    HEART_BASE = HEART_HIT = HEART_DGD = None
    HEART_LOADED = False

# ── Sidebar character images ─────────────────────────────────────────────────
def _load_sidebar(filename):
    try:
        raw = pygame.image.load(filename).convert_alpha()
        h   = GH
        w   = int(raw.get_width() * h / raw.get_height())
        return pygame.transform.smoothscale(raw, (w, h))
    except (pygame.error, FileNotFoundError):
        return None

IMG_SANS      = _load_sidebar("sans.png")
IMG_SPAMTON   = _load_sidebar("spamtonneo.png")
IMG_UNDYNE    = _load_sidebar("Undyne.png")
IMG_ASRIEL    = _load_sidebar("asriel.png")
IMG_ROARINGKNIGHT = _load_sidebar("RoaringKnight.png")
IMG_METATON   = _load_sidebar("MattatonEX.png")

# ═══════════════════════════════════════════════════════════════════════════
#  SOUNDS  (synthesised – no external files needed)
# ═══════════════════════════════════════════════════════════════════════════
def _tone(freq, dur_ms, vol=0.25, overtones=None):
    """Generate a short synthesised tone as a pygame Sound."""
    sr  = 44100
    n   = int(sr * dur_ms / 1000)
    buf = bytearray(n * 4)   # stereo, 16-bit → 4 bytes per frame
    ots = overtones or [(1.0, 1.0)]
    for i in range(n):
        t_sec = i / sr
        env   = min(1.0, t_sec / 0.005) * math.exp(-t_sec * 14)
        raw   = sum(a * math.sin(2 * math.pi * freq * m * i / sr) for m, a in ots)
        v     = int(vol * 32767 * env * raw / len(ots))
        v     = max(-32768, min(32767, v))
        lo, hi = struct.pack("<h", v)
        buf[i*4:i*4+4] = [lo, hi, lo, hi]
    return pygame.mixer.Sound(buffer=bytes(buf))

SND_WARN  = _tone(740,  75, 0.20, [(1, 1.0), (2, 0.3)])
SND_ATCK  = _tone(200, 110, 0.28, [(1, 1.0), (3, 0.4)])
SND_MISS  = _tone(100, 210, 0.25, [(1, 1.0), (1.5, 0.5)])
SND_DODGE = _tone(960,  55, 0.14, [(1, 1.0), (2, 0.2)])
SND_START = _tone(528, 190, 0.22)
SND_END   = _tone(440, 280, 0.18, [(1, 1.0), (1.25, 0.5), (1.5, 0.25)])



# ═══════════════════════════════════════════════════════════════════════════
#  LEVEL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════
LEVELS = [
    {
        'name':     'His Theme',
        'subtitle': '153 BPM  \u00b7  40 s  \u00b7  Easy',
        'bpm':      153,
        'music':    'HisTheme.ogg',
        'data':     level_histheme.build_level(),
        'sidebar':  IMG_ASRIEL,
    },
    {
        'name':     '[[BIG SHOT]]',
        'subtitle': '140 BPM  \u00b7  40 s  \u00b7  Medium',
        'bpm':      140,
        'music':    'BIGSHOT.ogg',
        'data':     level_bigshot.build_level(),
        'sidebar':  IMG_SPAMTON,
    },
    {
        'name':     'Megalovania',
        'subtitle': '120 BPM  \u00b7  40 s  \u00b7  Medium',
        'bpm':      120,
        'music':    'Megalovania.ogg',
        'data':     level_megalovania.build_level(warn_beats=2),
        'sidebar':  IMG_SANS,
    },
    {
        'name':     'A Battle Against a True Hero',
        'subtitle': '150 BPM  \u00b7  40 s  \u00b7  Medium',
        'bpm':      150,
        'music':    'BattleAgainstATrueHero.ogg',
        'data':     level_undyne.build_level(),
        'sidebar':  IMG_UNDYNE,
    },
    {
        'name':     'Black Knife',
        'subtitle': '147.5 BPM  \u00b7  40 s  \u00b7  Hard',
        'bpm':      147.5,
        'music':    'BlackKnife.ogg',
        'data':     level_blackknife.build_level(warn_beats=1),
        'sidebar':  IMG_ROARINGKNIGHT,
    },
    {
        'name':     'Death By Glamour',
        'subtitle': '148 BPM  \u00b7  40 s  \u00b7  Hard',
        'bpm':      120,
        'music':    'deathbyglamour.ogg',
        'data':     level_deathbyglamour.build_level(warn_beats=1),
        'sidebar':  IMG_METATON,
    },
]



# ═══════════════════════════════════════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════════════════════════════════════
class Player:
    MOVE_SPEED = 1400   # pixels per second for smooth glide

    def __init__(self):
        self.pos        = CENTER
        self.held       = []
        self.held_btns  = []
        self.flash = 0
        self.glow  = 0
        r, c = CENTER
        _r = cell_rect(r, c)
        self.px = float(_r.centerx)
        self.py = float(_r.centery)

    def _target_pixel(self):
        r, c = self.pos
        rect = cell_rect(r, c)
        return float(rect.centerx), float(rect.centery)

    def key_down(self, key):
        if key in KEY_POS and key not in self.held:
            self.held.append(key)
            self.pos = KEY_POS[key]

    def key_up(self, key):
        if key in self.held:
            self.held.remove(key)
            self.pos = KEY_POS[self.held[-1]] if self.held else CENTER

    def joy_down(self, btn):
        if btn in BTN_POS and btn not in self.held_btns:
            self.held_btns.append(btn)
            self.pos = BTN_POS[btn]

    def joy_up(self, btn):
        if btn in self.held_btns:
            self.held_btns.remove(btn)
            self.pos = BTN_POS[self.held_btns[-1]] if self.held_btns else CENTER

    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        self.glow  = max(0, self.glow  - dt)
        tx, ty = self._target_pixel()
        dx, dy = tx - self.px, ty - self.py
        dist   = math.hypot(dx, dy)
        step   = self.MOVE_SPEED * dt / 1000.0
        if dist <= step:
            self.px, self.py = tx, ty
        else:
            self.px += dx / dist * step
            self.py += dy / dist * step

    @property
    def tint(self):
        if self.flash > 0: return C_PLR_HIT
        if self.glow  > 0: return C_PLR_DGD
        return C_PLR

    def draw(self, surf):
        cx, cy = int(self.px), int(self.py)

        if HEART_LOADED:
            half = _HEART_PX // 2
            if self.flash > 0:
                pygame.draw.circle(surf, (200, 38, 38), (cx, cy), half + 13)
            elif self.glow > 0:
                pygame.draw.circle(surf, (32, 150, 72), (cx, cy), half + 13)
            if self.flash > 0:
                img = HEART_HIT
            elif self.glow > 0:
                img = HEART_DGD
            else:
                img = HEART_BASE
            surf.blit(img, (cx - half, cy - half))
        else:
            rad = CELL // 2 - 14
            if self.flash > 0:
                pygame.draw.circle(surf, (200, 38, 38), (cx, cy), rad + 11)
            elif self.glow > 0:
                pygame.draw.circle(surf, (32, 150, 72), (cx, cy), rad + 11)
            pygame.draw.circle(surf, self.tint, (cx, cy), rad)
            pygame.draw.circle(surf, WHITE, (cx - rad//3, cy - rad//3), rad // 5)
            pygame.draw.circle(surf, (180, 240, 255), (cx, cy), rad, 2)


# ═══════════════════════════════════════════════════════════════════════════
#  SCORE POPUP
# ═══════════════════════════════════════════════════════════════════════════
class Popup:
    def __init__(self, text, color, x, y, life_ms=820):
        self.text  = text
        self.color = color
        self.x     = float(x)
        self.y     = float(y)
        self.life  = float(life_ms)
        self.total = float(life_ms)

    def update(self, dt):
        self.life -= dt
        self.y    -= dt * 0.042

    @property
    def alive(self): return self.life > 0

    def draw(self, surf):
        a   = int(255 * max(0.0, self.life / self.total))
        img = F_MED.render(self.text, True, self.color)
        img.set_alpha(a)
        surf.blit(img, (int(self.x) - img.get_width()//2, int(self.y)))


# ═══════════════════════════════════════════════════════════════════════════
#  DRAW UTILITIES
# ═══════════════════════════════════════════════════════════════════════════
def blit_text(surf, text, font, color, cx, cy, anchor='center'):
    img  = font.render(str(text), True, color)
    rect = img.get_rect()
    setattr(rect, anchor, (cx, cy))
    surf.blit(img, rect)
    return rect


def draw_grid(surf, grid, sprites, t_ms, pre_atk=None):
    pre_atk    = pre_atk or set()
    any_real_danger = any(grid[r][c] in (WARN, ATCK) for r in range(3) for c in range(3))
    for r in range(3):
        for c in range(3):
            rect  = cell_rect(r, c)
            state = grid[r][c]

            if state == SAFE:
                col = C_SAFE_GRN if any_real_danger else C_SAFE
            elif state == FAKE_WARN:
                col = C_FAKE_WARN
            elif state == WARN:
                if (r, c) in pre_atk:
                    # Pulse from yellow toward red as the attack approaches
                    p   = (math.sin(t_ms * 0.06) + 1) * 0.5
                    col = (
                        min(255, int(C_WARN[0] + (C_HIT[0] - C_WARN[0]) * p)),
                        max(0,   int(C_WARN[1] + (C_HIT[1] - C_WARN[1]) * p)),
                        max(0,   int(C_WARN[2] + (C_HIT[2] - C_WARN[2]) * p)),
                    )
                else:
                    col = C_WARN
            else:
                p   = (math.sin(t_ms * 0.032) + 1) * 0.5
                col = (
                    min(255, int(C_HIT[0] + 28 * p)),
                    max(0,   int(C_HIT[1] - 10 * p)),
                    max(0,   int(C_HIT[2] - 5  * p)),
                )

            pygame.draw.rect(surf, col,      rect, border_radius=11)
            pygame.draw.rect(surf, C_BORDER, rect, 2, border_radius=11)

    for spr in sprites:
        cells = spr.get('cells', [])
        color = spr.get('color', GOLD)
        alpha = spr.get('alpha', 190)
        label = spr.get('label', '')
        if not cells:
            continue
        rects = [cell_rect(r, c) for r, c in cells]
        for rect in rects:
            ovl = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            ovl.fill((*color, alpha // 2))
            surf.blit(ovl, rect.topleft)
        if label and rects:
            cx = sum(rc.centerx for rc in rects) // len(rects)
            cy = sum(rc.centery for rc in rects) // len(rects)
            lbl = F_BIG.render(label, True, color)
            lbl.set_alpha(alpha)
            surf.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))


def draw_hud(surf, score, elapsed_ms, total_ms, streak):
    blit_text(surf, f"SCORE  {score:>6}", F_MED, WHITE,  58, 26, 'topleft')
    if streak >= 3:
        blit_text(surf, f"STREAK  {streak}", F_SM, TEAL, 60, 64, 'topleft')

    bx, by, bw, bh = GX, GY + GH + 20, GW, 10
    pct = max(0.0, 1.0 - elapsed_ms / max(1, total_ms))
    pygame.draw.rect(surf, DK_GRAY, (bx, by, bw, bh),              border_radius=5)
    pygame.draw.rect(surf, PURPLE,  (bx, by, int(bw * pct), bh),   border_radius=5)

    secs_left = max(0.0, (total_ms - elapsed_ms) / 1000.0)
    blit_text(surf, f"{secs_left:05.2f}s", F_XS, GRAY, bx + bw + 10, by - 1, 'topleft')


def draw_sidebar(surf, img):
    if img is None:
        return
    x = GX + GW + 40
    y = GY
    surf.blit(img, (x, y))


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: TITLE
# ═══════════════════════════════════════════════════════════════════════════
def screen_start():
    t = 0
    while True:
        dt = clock.tick(FPS)
        t += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit'
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: return 'quit'
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE): return 'select'
            if ev.type == pygame.JOYBUTTONDOWN:
                return 'select'

        screen.fill(BG)

        for r in range(3):
            for c in range(3):
                rect  = cell_rect(r, c)
                phase = (r * 3 + c) * 370
                p     = (math.sin((t + phase) * 0.0020) + 1) * 0.5
                col   = tuple(int(C_SAFE[i] * (0.55 + 0.45 * p)) for i in range(3))
                pygame.draw.rect(screen, col,      rect, border_radius=11)
                pygame.draw.rect(screen, C_BORDER, rect, 2, border_radius=11)

        tp  = (math.sin(t * 0.0026) + 1) * 0.5
        tc  = tuple(int(PURPLE[i] * (0.68 + 0.32 * tp)) for i in range(3))
        blit_text(screen, "KGB x Roboclub", F_HUGE, tc, SW//2, 85)
        blit_text(screen, "Toby Fox Game", F_SM, GRAY, SW//2, 155)

        # ── Controls description ──────────────────────────────────────────
        for line_i, (txt, col) in enumerate([
            ("CONTROLS", WHITE),
            ("Each DDR pad direction maps to a grid square", GRAY),
            ("Letting go snaps you back to the center square", GRAY),
        ]):
            blit_text(screen, txt, F_SM if line_i > 0 else F_BIG, col,
                      SW//2, SH - 250 + line_i * 52)

        if (t // 500) % 2 == 0:
            blit_text(screen, "PRESS  ENTER  TO  START", F_MED, WHITE, SW//2, SH - 42)

        _present()


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: TUTORIAL
# ═══════════════════════════════════════════════════════════════════════════
def screen_tutorial():
    """3-page tutorial.  Returns 'select' to continue, 'back' for start."""
    page       = 0
    PAGE_COUNT = 3
    t          = 0

    # Page 0 – animated player walking around the grid
    DEMO_PATH = [
        (1,1),(0,1),(1,1),(1,2),(1,1),(2,1),(1,1),(1,0),
        (1,1),(0,0),(1,1),(0,2),(1,1),(2,2),(1,1),(2,0),
    ]
    demo_idx   = 0
    demo_timer = 0
    DEMO_STEP  = 550   # ms per step

    DIR_LABELS = [
        ["↖", "↑", "↗"],
        ["←", "●", "→"],
        ["↙", "↓", "↘"],
    ]

    # Scaled heart for the mini-grid
    MINI  = 110
    GAP2  = 6
    H_SZ  = MINI - 30
    if HEART_LOADED:
        heart_mini = pygame.transform.smoothscale(HEART_BASE, (H_SZ, H_SZ))
    else:
        heart_mini = None

    while True:
        dt = clock.tick(FPS)
        t          += dt
        demo_timer += dt
        if demo_timer >= DEMO_STEP:
            demo_timer -= DEMO_STEP
            demo_idx    = (demo_idx + 1) % len(DEMO_PATH)
        demo_pos = DEMO_PATH[demo_idx]

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'back'
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    return 'back'
                if k in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE, pygame.K_d):
                    if page < PAGE_COUNT - 1:
                        page += 1
                    else:
                        return 'select'
                if k in (pygame.K_LEFT, pygame.K_a):
                    page = max(0, page - 1)
            if ev.type == pygame.JOYHATMOTION:
                if ev.value[0] ==  1: page = min(PAGE_COUNT - 1, page + 1)
                if ev.value[0] == -1: page = max(0, page - 1)
            if ev.type == pygame.JOYBUTTONDOWN:
                if page < PAGE_COUNT - 1:
                    page += 1
                else:
                    return 'select'

        screen.fill(BG)

        # ── Page dots ────────────────────────────────────────────────────────
        for pi in range(PAGE_COUNT):
            cx  = SW // 2 + (pi - PAGE_COUNT // 2) * 30
            col = WHITE if pi == page else DK_GRAY
            pygame.draw.circle(screen, col, (cx, 56), 7)

        # ── ESC hint ─────────────────────────────────────────────────────────
        blit_text(screen, "ESC  Back", F_XS, GRAY, SW - 30, 28, 'topright')

        # ════════════════════════════════════════════════════════════════════
        if page == 0:
            # ── PAGE 0: MOVEMENT ─────────────────────────────────────────────
            blit_text(screen, "MOVEMENT", F_BIG, PURPLE, SW // 2, 108)

            MGW = MINI * 3 + GAP2 * 2
            MGH = MINI * 3 + GAP2 * 2
            MGX = (SW - MGW) // 2
            MGY = (SH - MGH) // 2 - 50

            for r in range(3):
                for c in range(3):
                    rx   = MGX + c * (MINI + GAP2)
                    ry   = MGY + r * (MINI + GAP2)
                    rect = pygame.Rect(rx, ry, MINI, MINI)
                    is_p = (r, c) == demo_pos
                    col  = (60, 48, 100) if is_p else C_SAFE
                    pygame.draw.rect(screen, col,      rect, border_radius=10)
                    pygame.draw.rect(screen, C_BORDER, rect, 2,  border_radius=10)
                    lbl_col = WHITE if is_p else GRAY
                    blit_text(screen, DIR_LABELS[r][c], F_MED, lbl_col,
                              rx + MINI // 2, ry + MINI // 2)

            # Heart on demo_pos
            pr, pc = demo_pos
            hx = MGX + pc * (MINI + GAP2) + MINI // 2
            hy = MGY + pr * (MINI + GAP2) + MINI // 2
            if heart_mini:
                screen.blit(heart_mini, (hx - H_SZ // 2, hy - H_SZ // 2))
            else:
                pygame.draw.circle(screen, C_PLR, (hx, hy), 24)

            blit_text(screen, "Each DDR pad direction moves to that grid square.",
                      F_SM, WHITE, SW // 2, MGY + MGH + 50)
            blit_text(screen, "Releasing any direction snaps you back to center.",
                      F_SM, GRAY,  SW // 2, MGY + MGH + 88)

        # ════════════════════════════════════════════════════════════════════
        elif page == 1:
            # ── PAGE 1: WARNINGS & ATTACKS ───────────────────────────────────
            blit_text(screen, "WARNINGS  &  ATTACKS", F_BIG, PURPLE, SW // 2, 108)

            DC   = 170   # demo cell size
            DGAP = 90
            tot  = DC * 3 + DGAP * 2
            sx   = (SW - tot) // 2
            cy   = SH // 2 - 20

            demos = [
                (SAFE, "SAFE",    GREEN, "You're in the clear."),
                (WARN, "WARNING", GOLD,  "Attack incoming — move soon!"),
                (ATCK, "ATTACK",  RED,   "Get off this square NOW!"),
            ]
            for i, (state, label, col, tip) in enumerate(demos):
                cx   = sx + i * (DC + DGAP) + DC // 2
                rect = pygame.Rect(cx - DC // 2, cy - DC // 2, DC, DC)

                if state == SAFE:
                    cell_col = C_SAFE_GRN
                elif state == WARN:
                    cell_col = C_WARN
                else:
                    p        = (math.sin(t * 0.032) + 1) * 0.5
                    cell_col = (
                        min(255, int(C_HIT[0] + 28 * p)),
                        max(0,   int(C_HIT[1] - 10 * p)),
                        max(0,   int(C_HIT[2] -  5 * p)),
                    )

                pygame.draw.rect(screen, cell_col, rect, border_radius=14)
                pygame.draw.rect(screen, C_BORDER,  rect, 3,  border_radius=14)
                blit_text(screen, label, F_MED, col, cx, cy + DC // 2 + 36)
                blit_text(screen, tip,   F_XS,  GRAY, cx, cy + DC // 2 + 76)

            blit_text(screen,
                      "Squares pulse yellow briefly before an attack, then turn red.",
                      F_SM, WHITE, SW // 2, SH - 150)
            blit_text(screen,
                      "You have a short window after the warning to step away.",
                      F_SM, GRAY,  SW // 2, SH - 108)

        # ════════════════════════════════════════════════════════════════════
        elif page == 2:
            # ── PAGE 2: SCORING & TIPS ───────────────────────────────────────
            blit_text(screen, "SCORING  &  TIPS", F_BIG, PURPLE, SW // 2, 108)

            score_lines = [
                ("+1 per frame  on a safe square", GREEN),
                ("-100          when hit by an attack", RED),
                ("STREAK        3+ hits dodged in a row", TEAL),
            ]
            for i, (txt, col) in enumerate(score_lines):
                blit_text(screen, txt, F_SM, col, SW // 2, 310 + i * 82)

            tip_lines = [
                ("Watch the progress bar below the grid — it counts down the song.",
                 GRAY),
                ("You can return to the menu mid-level with ESC.", GRAY),
                ("Good luck!", WHITE),
            ]
            for i, (txt, col) in enumerate(tip_lines):
                blit_text(screen, txt, F_XS, col, SW // 2, 570 + i * 52)

        # ── Navigation hint ──────────────────────────────────────────────────
        if (t // 500) % 2 == 0:
            if page < PAGE_COUNT - 1:
                blit_text(screen, "ENTER / →  Next",  F_SM, WHITE, SW // 2, SH - 46)
            else:
                blit_text(screen, "ENTER  Play!", F_MED, WHITE, SW // 2, SH - 46)

        _present()


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: LEVEL SELECT
# ═══════════════════════════════════════════════════════════════════════════
def screen_level_select():
    sel = 0
    while True:
        dt = clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return 'back'
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:                   return 'back'
                if k in (pygame.K_UP,   pygame.K_w):       sel = (sel - 1) % len(LEVELS)
                if k in (pygame.K_DOWN, pygame.K_s):       sel = (sel + 1) % len(LEVELS)
                if k in (pygame.K_RETURN, pygame.K_SPACE): return sel
            if ev.type == pygame.JOYHATMOTION:
                if ev.value[1] ==  1: sel = (sel - 1) % len(LEVELS)
                if ev.value[1] == -1: sel = (sel + 1) % len(LEVELS)
            if ev.type == pygame.JOYBUTTONDOWN:
                return sel

        screen.fill(BG)
        blit_text(screen, "SELECT  LEVEL", F_BIG, PURPLE, SW//2, 80)

        for i, lv in enumerate(LEVELS):
            y      = 220 + i * 120
            is_sel = (i == sel)
            bg     = (48, 38, 78) if is_sel else (22, 17, 38)
            rect   = pygame.Rect(SW//2 - 320, y - 36, 640, 84)
            pygame.draw.rect(screen, bg, rect, border_radius=14)
            if is_sel:
                pygame.draw.rect(screen, PURPLE, rect, 3, border_radius=14)
            col = WHITE if is_sel else GRAY
            blit_text(screen, lv['name'],     F_MED, col,  SW//2, y - 6)
            blit_text(screen, lv['subtitle'], F_SM,  GRAY, SW//2, y + 32)

        blit_text(screen, "↑ ↓  Navigate    ENTER  Select    ESC  Back",
                  F_SM, GRAY, SW//2, SH - 44)
        _present()


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: GAMEPLAY
# ═══════════════════════════════════════════════════════════════════════════
def screen_game(level_idx):
    level    = LEVELS[level_idx]
    data     = level['data']
    sidebar  = level.get('sidebar')
    total_ms = sum(s['duration'] for s in data)

    # ── Music ─────────────────────────────────────────────────────────────
    # Place the music file in the same folder as this script.
    # .m4a support depends on your SDL_mixer build. If it fails, convert to
    # .ogg (ffmpeg -i "file.m4a" "file.ogg") and update the 'music' key.
    import os
    music_file = level.get('music', '')
    music_ok   = False
    if music_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        music_path = os.path.join(script_dir, music_file)
        if not os.path.isfile(music_path):
            print(f"[MUSIC] File not found: {music_path}")
        else:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.75)
                pygame.mixer.music.play()
                music_ok = True
                print(f"[MUSIC] Playing: {music_path}")
            except Exception as e:
                print(f"[MUSIC] Failed for '{music_path}': {e}")
                print("[MUSIC] Tip: convert to .ogg for guaranteed SDL_mixer support")

    player  = Player()
    score   = 0
    streak  = 0

    popups        = []
    seg_idx       = 0
    seg_timer     = 0.0
    elapsed       = 0.0
    pulse_t       = 0.0
    prev_grid     = [[SAFE]*3 for _ in range(3)]
    was_in_attack = False

    SND_START.play()

    while True:
        dt = clock.tick(FPS)
        pulse_t   += dt
        elapsed   += dt
        seg_timer += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                if music_ok: pygame.mixer.music.stop()
                return score, 'quit'
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if music_ok: pygame.mixer.music.stop()
                    return score, 'back'
                else:
                    player.key_down(ev.key)
            if ev.type == pygame.KEYUP:
                player.key_up(ev.key)
            if ev.type == pygame.JOYHATMOTION:
                pos = HAT_POS.get(ev.value)
                if pos is not None:
                    player.pos = pos
            if ev.type == pygame.JOYBUTTONDOWN:
                player.joy_down(ev.button)
            if ev.type == pygame.JOYBUTTONUP:
                player.joy_up(ev.button)
            if ev.type == pygame.JOYAXISMOTION:
                if ev.axis == 0: _joy_axes[0] = ev.value
                if ev.axis == 1: _joy_axes[1] = ev.value
                player.pos = _axes_to_pos()

        while seg_idx < len(data) and seg_timer >= data[seg_idx]['duration']:
            seg_timer -= data[seg_idx]['duration']
            seg_idx   += 1

        if seg_idx >= len(data):
            break

        cur     = data[seg_idx]
        grid    = cur['grid']
        sprites = cur['sprites']

        # Cells currently WARN that will become ATCK next segment
        pre_atk = set()
        if seg_idx + 1 < len(data):
            next_grid  = data[seg_idx + 1]['grid']
            time_ratio = seg_timer / max(1, cur['duration'])
            if time_ratio > 0.5:   # only flash in the second half of the warn beat
                for _r in range(3):
                    for _c in range(3):
                        if grid[_r][_c] == WARN and next_grid[_r][_c] == ATCK:
                            pre_atk.add((_r, _c))

        for r in range(3):
            for c in range(3):
                old, new = prev_grid[r][c], grid[r][c]
                if old not in (WARN, FAKE_WARN) and new in (WARN, FAKE_WARN):
                    SND_WARN.play()
                    break
                if old == WARN and new == ATCK:
                    SND_ATCK.play()
                    break

        pr, pc     = player.pos
        cell_state = grid[pr][pc]
        now_hit    = (cell_state == ATCK)

        if now_hit and not was_in_attack:
            player.flash  = 440
            score        -= 100
            streak        = 0
            SND_MISS.play()
            rx, ry = cell_rect(pr, pc).center
            popups.append(Popup("-100", RED, rx, ry - 32))
        elif not now_hit:
            score += 1
            

        was_in_attack = now_hit
        prev_grid     = [row[:] for row in grid]

        player.update(dt)
        for p in popups: p.update(dt)
        popups = [p for p in popups if p.alive]

        screen.fill(BG)
        draw_grid(screen, grid, sprites, pulse_t, pre_atk)
        player.draw(screen)
        draw_hud(screen, score, elapsed, total_ms, streak)
        draw_sidebar(screen, sidebar)
        for p in popups: p.draw(screen)
        _present()

    if music_ok: pygame.mixer.music.stop()
    SND_END.play()
    return score, 'end'


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: END
# ═══════════════════════════════════════════════════════════════════════════
def screen_end(score):
    t = 0

    for threshold, grade, gcol in [
        (2000, 'S', GOLD),
        (1500, 'A', GREEN),
        (1000, 'B', PURPLE),
        (500,  'C', WHITE),
        (0,    'D', RED),
    ]:
        if score >= threshold:
            break

    descs = {'S': 'Youre a [[BIG SHOT]]!!!', 'A': 'You are filled with determination', 'B': 'NYEH HEH HEEEEH', 'C': 'Frozen Spaghetti...', 'D': 'You ate the Moss'}

    while True:
        dt = clock.tick(FPS)
        t += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        return 'quit'
            if ev.type == pygame.KEYDOWN:     return 'menu'
            if ev.type == pygame.JOYBUTTONDOWN: return 'menu'

        screen.fill(BG)

        blit_text(screen, "LEVEL  CLEAR !",    F_BIG,  PURPLE, SW//2,  90)
        blit_text(screen, "FINAL SCORE",        F_SM,   GRAY,   SW//2, 178)
        blit_text(screen, str(score),           F_HUGE, WHITE,  SW//2, 252)

        p   = (math.sin(t * 0.004) + 1) * 0.5
        gp  = tuple(int(gcol[i] * (0.68 + 0.32 * p)) for i in range(3))
        blit_text(screen, grade,               F_GRADE, gp,    SW//2, 370)
        blit_text(screen, descs.get(grade,''), F_SM,   gcol,   SW//2, 462)

        if (t // 580) % 2 == 0:
            blit_text(screen, "PRESS  ANY  KEY  to return to menu",
                      F_SM, GRAY, SW//2, SH - 46)

        _present()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
def main():
    state      = 'start'
    level_idx  = 0
    last_score = 0

    while True:
        if state == 'start':
            result = screen_start()
            if result == 'select': state = 'tutorial'
            else:                  state = None

        elif state == 'tutorial':
            result = screen_tutorial()
            if result == 'select': state = 'select'
            elif result == 'back': state = 'start'
            else:                  state = None

        elif state == 'select':
            result = screen_level_select()
            if isinstance(result, int):
                level_idx = result
                state     = 'game'
            elif result == 'back':
                state = 'start'
            else:
                state = None

        elif state == 'game':
            last_score, result = screen_game(level_idx)
            if result == 'end':    state = 'end'
            elif result == 'back': state = 'start'
            else:                  state = None

        elif state == 'end':
            result = screen_end(last_score)
            state  = 'start' if result == 'menu' else None

        if state is None:
            break

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()