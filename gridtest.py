import pygame
import sys
import math
import struct

# ═══════════════════════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

SW, SH = 1920, 1080
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Grid Dodge")
clock  = pygame.time.Clock()
FPS    = 60

# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════════════════════
BG        = ( 12,   9,  22)
C_SAFE    = ( 32,  26,  55)
C_WARN    = (195, 138,   8)
C_HIT     = (188,  34,  34)
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
#  SQUARE STATES
# ═══════════════════════════════════════════════════════════════════════════
SAFE = 0   # all clear
WARN = 1   # attack incoming (warning / pre-flash)
ATCK = 2   # actively attacked

# ═══════════════════════════════════════════════════════════════════════════
#  CONTROLS  (DDR pad mapped to keyboard)
# ═══════════════════════════════════════════════════════════════════════════
#   U I O   →   (0,0) (0,1) (0,2)
#   J   L   →   (1,0)       (1,2)
#   M , .   →   (2,0) (2,1) (2,2)
KEY_POS = {
    pygame.K_u: (0, 0),   pygame.K_i: (0, 1),   pygame.K_o: (0, 2),
    pygame.K_j: (1, 0),                           pygame.K_l: (1, 2),
    pygame.K_m: (2, 0),   pygame.K_COMMA: (2, 1), pygame.K_PERIOD: (2, 2),
}
CENTER = (1, 1)

# ═══════════════════════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════════════════════
def _font(size, bold=False):
    for name in ("Consolas", "Courier New", "monospace"):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

F_HUGE  = _font(76, True)
F_GRADE = _font(118, True)
F_BIG   = _font(50, True)
F_MED   = _font(34, True)
F_SM    = _font(23)
F_XS    = _font(17)

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
        # Amplitude envelope: short attack, exponential decay
        t_sec = i / sr
        env   = min(1.0, t_sec / 0.005) * math.exp(-t_sec * 14)
        raw   = sum(a * math.sin(2 * math.pi * freq * m * i / sr) for m, a in ots)
        v     = int(vol * 32767 * env * raw / len(ots))
        v     = max(-32768, min(32767, v))
        lo, hi = struct.pack("<h", v)
        buf[i*4:i*4+4] = [lo, hi, lo, hi]   # L + R identical
    return pygame.mixer.Sound(buffer=bytes(buf))

SND_WARN  = _tone(740,  75, 0.20, [(1, 1.0), (2, 0.3)])
SND_ATCK  = _tone(200, 110, 0.28, [(1, 1.0), (3, 0.4)])
SND_MISS  = _tone(100, 210, 0.25, [(1, 1.0), (1.5, 0.5)])
SND_DODGE = _tone(960,  55, 0.14, [(1, 1.0), (2, 0.2)])
SND_START = _tone(528, 190, 0.22)
SND_END   = _tone(440, 280, 0.18, [(1, 1.0), (1.25, 0.5), (1.5, 0.25)])

# ═══════════════════════════════════════════════════════════════════════════
#  LEVEL DATA FORMAT
# ═══════════════════════════════════════════════════════════════════════════
#
# level_data  = list of segment dicts
#
# segment dict = {
#   'duration' : int   – milliseconds this segment lasts
#   'grid'     : [[int,int,int],[int,int,int],[int,int,int]]
#                  values are SAFE / WARN / ATCK
#   'sprites'  : list of sprite dicts   (optional, default [])
# }
#
# sprite dict = {
#   'cells'  : [(row,col), ...]  – cells this sprite overlays
#   'color'  : (R,G,B)
#   'label'  : str               – drawn at centroid of cells  (optional)
#   'alpha'  : int 0-255         – overlay transparency
# }
# ═══════════════════════════════════════════════════════════════════════════

# ── Builder helpers ─────────────────────────────────────────────────────────

def _safe_grid():
    return [[SAFE, SAFE, SAFE], [SAFE, SAFE, SAFE], [SAFE, SAFE, SAFE]]

def _warn_grid(*cells):
    g = [SAFE] * 9
    for r, c in cells: g[r * 3 + c] = WARN
    return [g[0:3], g[3:6], g[6:9]]

def _hit_grid(*cells):
    g = [SAFE] * 9
    for r, c in cells: g[r * 3 + c] = ATCK
    return [g[0:3], g[3:6], g[6:9]]

def seg(dur, grid, sprites=None):
    """Create a single level segment dict."""
    return {'duration': dur, 'grid': grid, 'sprites': sprites or []}

def attack(total_ms, *cells, warn_ms=255, hit_ms=185, sprites=None):
    """
    Create a (warn → hit → rest) segment sequence summing to total_ms.
    sprites are shown during both warn and hit phases.
    """
    rest_ms = total_ms - warn_ms - hit_ms
    if rest_ms < 0:
        # Clamp: shorten rest, never allow negative
        warn_ms = int(total_ms * 0.58)
        hit_ms  = total_ms - warn_ms
        rest_ms = 0
    sp = sprites or []
    out = [
        seg(warn_ms, _warn_grid(*cells), sp),
        seg(hit_ms,  _hit_grid(*cells),  sp),
    ]
    if rest_ms > 0:
        out.append(seg(rest_ms, _safe_grid()))
    return out

def mk_sprite(cells, color, label='', alpha=190):
    return {'cells': list(cells), 'color': color, 'label': label, 'alpha': alpha}

ARROWS = {
    'r': '→', 'l': '←', 'u': '↑', 'd': '↓',
    'ul': '↖', 'ur': '↗', 'dl': '↙', 'dr': '↘', 'x': '✕', 'o': '●',
}

def arrow_sp(cells, direction, color=GOLD):
    return mk_sprite(cells, color, ARROWS.get(direction, '?'), 215)

# ═══════════════════════════════════════════════════════════════════════════
#  TEST LEVEL  ≈ 40 seconds at 120 BPM
# ═══════════════════════════════════════════════════════════════════════════
def _build_test_level():
    BT = 750          # 1 beat window (ms) – widened to fit doubled warn
    W, H = 510, 185   # warn doubled (255→510); hit unchanged

    def a(*cells, beats=1, w=W, h=H, sp=None):
        """Standard 1-beat (or n-beat) attack."""
        return attack(BT * beats, *cells, warn_ms=w, hit_ms=h, sprites=sp)

    def q(*cells, sp=None):
        """Half-beat quick attack – warn also doubled (128→256)."""
        return attack(BT // 2, *cells, warn_ms=256, hit_ms=118, sprites=sp)

    segs = []
    add  = segs.extend   # shorthand

    # ── INTRO: 2 s (rest, let player get oriented) ────────────────────────
    segs.append(seg(2000, _safe_grid()))

    # ── PHASE 1 – Single cells; teach the grid  (12 beats = 6 s) ─────────
    for cells in [
        [(0, 0)], [(0, 2)], [(2, 0)], [(2, 2)],      # four corners
        [(0, 1)], [(1, 0)], [(1, 2)], [(2, 1)],      # four edges
        [(0, 0), (2, 2)],                              # diagonal pair
        [(0, 2), (2, 0)],                              # anti-diagonal pair
        [(0, 1), (2, 1)],                              # top+bottom edge
        [(1, 0), (1, 2)],                              # left+right edge
    ]:
        add(a(*cells))

    # brief rest between phases
    segs.append(seg(500, _safe_grid()))

    # ── PHASE 2 – Rows & columns  (8 beats = 4 s) ────────────────────────
    add(a((0,0),(0,1),(0,2)))                # top row
    add(a((2,0),(2,1),(2,2)))                # bottom row
    add(a((0,0),(1,0),(2,0)))                # left column
    add(a((0,2),(1,2),(2,2)))                # right column
    add(a((0,0),(0,1),(0,2),(1,0),(2,0)))    # top + left L-shape
    add(a((0,2),(1,2),(2,2),(2,0),(2,1)))    # right + bottom L-shape
    add(a((0,1),(1,0),(1,1),(1,2),(2,1)))    # cross / plus shape
    add(a((0,0),(0,2),(2,0),(2,2),(1,1)))    # corners + centre (X-ish)

    segs.append(seg(500, _safe_grid()))

    # ── PHASE 3 – Diagonals with arrow sprites  (6 beats = 3 s) ──────────
    d1 = [(0,0),(1,1),(2,2)]
    d2 = [(0,2),(1,1),(2,0)]
    sp1 = [arrow_sp(d1, 'dr', (255, 160, 40))]
    sp2 = [arrow_sp(d2, 'dl', (255, 160, 40))]

    add([
        seg(W,       _warn_grid(*d1), sp1),
        seg(H,       _hit_grid(*d1),  sp1),
        seg(BT-W-H,  _safe_grid()),
        seg(W,       _warn_grid(*d2), sp2),
        seg(H,       _hit_grid(*d2),  sp2),
        seg(BT-W-H,  _safe_grid()),
    ])

    # Full X pattern – only edge midpoints safe
    x_cells = [(0,0),(1,1),(2,2),(0,2),(2,0)]
    x_sp    = [mk_sprite(x_cells, ORANGE, ARROWS['x'], 200)]
    add([
        seg(W*2,          _warn_grid(*x_cells), x_sp),
        seg(H,            _hit_grid(*x_cells),  x_sp),
        seg(BT*2-W*2-H,   _safe_grid()),
    ])

    # Checkerboard alternation
    ck_a = [(0,0),(0,2),(1,1),(2,0),(2,2)]   # corners + centre
    ck_b = [(0,1),(1,0),(1,2),(2,1)]          # edge midpoints
    add(a(*ck_a))
    add(a(*ck_b))
    add(a(*ck_a))

    segs.append(seg(500, _safe_grid()))

    # ── PHASE 4 – Speed run: half-beat attacks  (8 attacks = 2 s) ────────
    for cells in [
        [(0,0)],          [(2,2)],
        [(0,2)],          [(2,0)],
        [(0,1),(2,1)],    [(1,0),(1,2)],
        d1,               d2,
    ]:
        add(q(*cells))

    segs.append(seg(500, _safe_grid()))

    # ── PHASE 5 – Complex multi-cell patterns  (10 beats = 5 s) ──────────
    add(a((0,0),(0,1),(0,2),(2,0),(2,1),(2,2)))             # top + bottom rows
    add(a((0,0),(1,0),(2,0),(0,2),(1,2),(2,2)))             # left + right columns
    add(a((0,0),(0,1),(1,0),(1,1)))                          # top-left quad
    add(a((0,1),(0,2),(1,1),(1,2)))                          # top-right quad
    add(a((1,0),(1,1),(2,0),(2,1)))                          # bottom-left quad
    add(a((1,1),(1,2),(2,1),(2,2)))                          # bottom-right quad
    add(a((0,0),(0,2),(1,0),(1,2),(2,0),(2,2)))              # outer ring without edges
    add(a((0,1),(1,0),(1,1),(1,2),(2,1),(0,0),(2,2)))        # 7 cells; only corners safe
    add(a((0,0),(0,1),(0,2),(1,0),(2,0),(2,1),(2,2),(1,2)))  # all but centre
    add(a((0,0),(0,2),(2,0),(2,2),(0,1),(2,1)))              # everything but side midpoints

    segs.append(seg(500, _safe_grid()))

    # ── PHASE 6 – Re-run with tighter timing  (8 half-beats = 2 s) ───────
    for cells in [
        [(0,0),(2,2)], [(0,2),(2,0)],
        [(0,1),(1,0),(1,2),(2,1)],
        [(0,0),(0,2),(1,1),(2,0),(2,2)],
        [(0,0),(0,1),(0,2)],
        [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)],
        [(0,2),(1,2),(2,2)],
    ]:
        add(q(*cells))

    segs.append(seg(500, _safe_grid()))

    # ── PHASE 7 – FINALE: big patterns, 3/4-beat rhythm  (8 × 375 ms = 3 s)
    finale_sp = [mk_sprite([(0,0),(1,1),(2,2),(0,2),(2,0)], RED, ARROWS['x'], 180)]
    for cells, sp in [
        ([(0,0),(0,2),(1,1),(2,0),(2,2)],      finale_sp),
        ([(0,1),(1,0),(1,2),(2,1)],            None),
        ([(0,0),(0,1),(0,2),(2,0),(2,1),(2,2)], None),
        ([(0,0),(1,0),(2,0),(0,2),(1,2),(2,2)], None),
        ([(0,0),(0,2),(1,1),(2,0),(2,2),(0,1),(2,1)], None),
        ([(0,1),(1,0),(1,2),(2,1),(1,1)],      None),
        ([(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)], None),
        ([(0,0),(0,2),(2,0),(2,2),(1,1),(0,1),(2,1)], finale_sp),
    ]:
        add(attack(750, *cells, warn_ms=390, hit_ms=160, sprites=sp))

    # ── OUTRO: pad to 40 s total ──────────────────────────────────────────
    total   = sum(s['duration'] for s in segs)
    target  = 60_000
    if total < target:
        segs.append(seg(target - total, _safe_grid()))

    return segs


# Level registry – add more levels here
LEVELS = [
    {
        'name':     'Test Level',
        'subtitle': '120 BPM  ·  60 seconds',
        'bpm':      120,
        'data':     _build_test_level(),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════════════════════════════════════
class Player:
    """
    Tracks position on the 3×3 grid.

    Movement rules:
      • Press a direction key → snap immediately to that cell.
      • Release a direction key:
          – If other keys are still held → snap to the most-recently-held.
          – If no keys held            → return to centre.
    """

    def __init__(self):
        self.pos   = CENTER   # (row, col)
        self.held  = []       # ordered list of currently held direction keys
        self.flash = 0        # ms of red damage flash
        self.glow  = 0        # ms of green dodge glow

    # ── Input ─────────────────────────────────────────────────────────────
    def key_down(self, key):
        if key in KEY_POS and key not in self.held:
            self.held.append(key)
            self.pos = KEY_POS[key]

    def key_up(self, key):
        if key in self.held:
            self.held.remove(key)
            self.pos = KEY_POS[self.held[-1]] if self.held else CENTER

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        self.glow  = max(0, self.glow  - dt)

    # ── Colour ────────────────────────────────────────────────────────────
    @property
    def tint(self):
        if self.flash > 0: return C_PLR_HIT
        if self.glow  > 0: return C_PLR_DGD
        return C_PLR

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, surf):
        r, c   = self.pos
        rect   = cell_rect(r, c)
        cx, cy = rect.centerx, rect.centery

        if HEART_LOADED:
            # ── Heart sprite path ────────────────────────────────────────
            half = _HEART_PX // 2

            # Glow disc drawn behind the sprite
            if self.flash > 0:
                pygame.draw.circle(surf, (200, 38, 38), (cx, cy), half + 13)
            elif self.glow > 0:
                pygame.draw.circle(surf, (32, 150, 72), (cx, cy), half + 13)

            # Pick the correctly tinted frame
            if self.flash > 0:
                img = HEART_HIT
            elif self.glow > 0:
                img = HEART_DGD
            else:
                img = HEART_BASE

            surf.blit(img, (cx - half, cy - half))

        else:
            # ── Fallback: plain circle (heart.png not found) ─────────────
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


def draw_grid(surf, grid, sprites, t_ms):
    """
    Render all 9 cells, then overlay any sprites.

    Cell colours:
      SAFE → deep purple                  (static)
      WARN → pulsing SAFE ↔ amber         (warning pulse)
      ATCK → harsh red flash              (attack flash)
    """
    for r in range(3):
        for c in range(3):
            rect  = cell_rect(r, c)
            state = grid[r][c]

            if state == SAFE:
                col = C_SAFE

            elif state == WARN:
                p   = (math.sin(t_ms * 0.013) + 1) * 0.5
                col = tuple(int(C_SAFE[i] + (C_WARN[i] - C_SAFE[i]) * p) for i in range(3))

            else:  # ATCK
                p   = (math.sin(t_ms * 0.032) + 1) * 0.5
                col = (
                    min(255, int(C_HIT[0] + 28 * p)),
                    max(0,   int(C_HIT[1] - 10 * p)),
                    max(0,   int(C_HIT[2] - 5  * p)),
                )

            pygame.draw.rect(surf, col,      rect, border_radius=11)
            pygame.draw.rect(surf, C_BORDER, rect, 2, border_radius=11)

    # ── Sprite overlays ─────────────────────────────────────────────────
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
    """Score, streak, and progress bar."""
    # Score (top-left)
    blit_text(surf, f"SCORE  {score:>6}", F_MED, WHITE,  58, 26, 'topleft')
    if streak >= 3:
        blit_text(surf, f"STREAK  {streak}", F_SM, TEAL, 60, 64, 'topleft')

    # Progress bar
    bx, by, bw, bh = GX, GY + GH + 20, GW, 10
    pct = max(0.0, 1.0 - elapsed_ms / max(1, total_ms))
    pygame.draw.rect(surf, DK_GRAY, (bx, by, bw, bh),              border_radius=5)
    pygame.draw.rect(surf, PURPLE,  (bx, by, int(bw * pct), bh),   border_radius=5)

    secs_left = max(0.0, (total_ms - elapsed_ms) / 1000.0)
    blit_text(surf, f"{secs_left:05.2f}s", F_XS, GRAY, bx + bw + 10, by - 1, 'topleft')


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: TITLE
# ═══════════════════════════════════════════════════════════════════════════
def screen_start():
    """Show the title screen. Returns 'select' or 'quit'."""
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

        screen.fill(BG)

        # Animated background grid
        for r in range(3):
            for c in range(3):
                rect  = cell_rect(r, c)
                phase = (r * 3 + c) * 370
                p     = (math.sin((t + phase) * 0.0020) + 1) * 0.5
                col   = tuple(int(C_SAFE[i] * (0.55 + 0.45 * p)) for i in range(3))
                pygame.draw.rect(screen, col,      rect, border_radius=11)
                pygame.draw.rect(screen, C_BORDER, rect, 2, border_radius=11)

        # Title
        tp  = (math.sin(t * 0.0026) + 1) * 0.5
        tc  = tuple(int(PURPLE[i] * (0.68 + 0.32 * tp)) for i in range(3))
        blit_text(screen, "wassah merlin", F_HUGE, tc, SW//2, 85)
        blit_text(screen, "Skibidi toilet", F_SM, GRAY, SW//2, 155)

        # Controls diagram
        blit_text(screen, "CONTROLS", F_SM, WHITE, SW//2, SH - 215)
        for label, (r, c) in [
            ('U',(0,0)),('I',(0,1)),('O',(0,2)),
            ('J',(1,0)),('·',(1,1)),('L',(1,2)),
            ('M',(2,0)),(',', (2,1)),('.',(2,2)),
        ]:
            kx = SW//2 - 65 + c * 44
            ky = SH - 185   + r * 36
            col = GOLD if label != '·' else GRAY
            pygame.draw.rect(screen, (28, 22, 48), (kx, ky, 38, 30), border_radius=5)
            pygame.draw.rect(screen, C_BORDER,     (kx, ky, 38, 30), 1, border_radius=5)
            blit_text(screen, label, F_SM, col, kx + 19, ky + 15)

        # Blinking prompt
        if (t // 500) % 2 == 0:
            blit_text(screen, "PRESS  ENTER  TO  START", F_MED, WHITE, SW//2, SH - 46)

        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: LEVEL SELECT
# ═══════════════════════════════════════════════════════════════════════════
def screen_level_select():
    """Show the level selection screen. Returns level index (int) or 'back'."""
    sel = 0
    while True:
        dt = clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return 'back'
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:                  return 'back'
                if k in (pygame.K_UP,   pygame.K_w):      sel = (sel - 1) % len(LEVELS)
                if k in (pygame.K_DOWN, pygame.K_s):      sel = (sel + 1) % len(LEVELS)
                if k in (pygame.K_RETURN, pygame.K_SPACE): return sel

        screen.fill(BG)
        blit_text(screen, "SELECT  LEVEL", F_BIG, PURPLE, SW//2, 80)

        for i, lv in enumerate(LEVELS):
            y     = 200 + i * 98
            is_sel = (i == sel)
            bg    = (48, 38, 78) if is_sel else (22, 17, 38)
            rect  = pygame.Rect(SW//2 - 230, y - 28, 460, 64)
            pygame.draw.rect(screen, bg, rect, border_radius=13)
            if is_sel:
                pygame.draw.rect(screen, PURPLE, rect, 2, border_radius=13)
            col = WHITE if is_sel else GRAY
            blit_text(screen, lv['name'],     F_MED, col,  SW//2, y - 4)
            blit_text(screen, lv['subtitle'], F_XS,  GRAY, SW//2, y + 24)

        blit_text(screen, "↑ ↓  Navigate    ENTER  Select    ESC  Back",
                  F_XS, GRAY, SW//2, SH - 38)
        pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: GAMEPLAY
# ═══════════════════════════════════════════════════════════════════════════
def screen_game(level_idx):
    """
    Main gameplay loop.
    Returns (final_score: int, next_state: str).
    next_state is one of 'end', 'back', 'quit'.
    """
    level    = LEVELS[level_idx]
    data     = level['data']
    total_ms = sum(s['duration'] for s in data)

    player  = Player()
    score   = 0
    streak  = 0          # consecutive attacks dodged without being hit

    popups  = []

    seg_idx   = 0
    seg_timer = 0.0
    elapsed   = 0.0
    pulse_t   = 0.0

    prev_grid    = [[SAFE]*3 for _ in range(3)]
    was_in_attack = False   # player was in an ATCK cell last frame

    SND_START.play()

    while True:
        dt = clock.tick(FPS)
        pulse_t  += dt
        elapsed  += dt
        seg_timer += dt

        # ── Events ─────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return score, 'quit'
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return score, 'back'
                player.key_down(ev.key)
            if ev.type == pygame.KEYUP:
                player.key_up(ev.key)

        # ── Advance level segments ──────────────────────────────────────────
        while seg_idx < len(data) and seg_timer >= data[seg_idx]['duration']:
            seg_timer -= data[seg_idx]['duration']
            seg_idx   += 1

        if seg_idx >= len(data):
            break   # level finished

        cur     = data[seg_idx]
        grid    = cur['grid']
        sprites = cur['sprites']

        # ── Play transition sounds ──────────────────────────────────────────
        for r in range(3):
            for c in range(3):
                old, new = prev_grid[r][c], grid[r][c]
                if old != WARN and new == WARN:
                    SND_WARN.play()
                    break
                if old == WARN and new == ATCK:
                    SND_ATCK.play()
                    break

        # ── Hit detection ───────────────────────────────────────────────────
        pr, pc     = player.pos
        cell_state = grid[pr][pc]
        now_hit    = (cell_state == ATCK)

        if now_hit and not was_in_attack:
            # Entered an attack square this frame
            player.flash  = 440
            score        -= 50
            streak        = 0
            SND_MISS.play()
            rx, ry = cell_rect(pr, pc).center
            popups.append(Popup("-50", RED, rx, ry - 32))

        elif not now_hit:
            # Safely surviving
            score += 1   # +1 pt per safe frame (~60/s)

            if was_in_attack:
                # Just escaped an attack phase → dodge bonus
                player.glow = 380
                score      += 30
                streak     += 1
                SND_DODGE.play()
                rx, ry = cell_rect(pr, pc).center
                popups.append(Popup("+30", GREEN, rx, ry - 32))

        was_in_attack = now_hit
        prev_grid     = [row[:] for row in grid]

        # ── Update ──────────────────────────────────────────────────────────
        player.update(dt)
        for p in popups: p.update(dt)
        popups = [p for p in popups if p.alive]

        # ── Draw ────────────────────────────────────────────────────────────
        screen.fill(BG)
        draw_grid(screen, grid, sprites, pulse_t)
        player.draw(screen)
        draw_hud(screen, score, elapsed, total_ms, streak)
        for p in popups: p.draw(screen)
        pygame.display.flip()

    SND_END.play()
    return score, 'end'


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: END
# ═══════════════════════════════════════════════════════════════════════════
def screen_end(score):
    """Show results screen. Returns 'menu' or 'quit'."""
    t = 0

    # Determine letter grade
    for threshold, grade, gcol in [
        (2400, 'S', GOLD),
        (1800, 'A', GREEN),
        (1200, 'B', PURPLE),
        (600,  'C', WHITE),
        (0,    'D', RED),
    ]:
        if score >= threshold:
            break

    descs = {'S': 'PERFECT!', 'A': 'EXCELLENT', 'B': 'GREAT', 'C': 'OK', 'D': 'KEEP TRYING'}

    while True:
        dt = clock.tick(FPS)
        t += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return 'quit'
            if ev.type == pygame.KEYDOWN: return 'menu'

        screen.fill(BG)

        blit_text(screen, "LEVEL  CLEAR !",  F_BIG,  PURPLE, SW//2,  90)
        blit_text(screen, "FINAL SCORE",      F_SM,   GRAY,   SW//2, 178)
        blit_text(screen, str(score),         F_HUGE, WHITE,  SW//2, 252)

        # Grade with pulse
        p   = (math.sin(t * 0.004) + 1) * 0.5
        gp  = tuple(int(gcol[i] * (0.68 + 0.32 * p)) for i in range(3))
        blit_text(screen, grade,             F_GRADE, gp,     SW//2, 370)
        blit_text(screen, descs.get(grade,''), F_SM,  gcol,   SW//2, 462)

        if (t // 580) % 2 == 0:
            blit_text(screen, "PRESS  ANY  KEY  to return to menu",
                      F_SM, GRAY, SW//2, SH - 46)

        pygame.display.flip()


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
            state  = 'select' if result == 'select' else None

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
            if result == 'end':   state = 'end'
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