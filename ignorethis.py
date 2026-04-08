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
#  SQUARE STATES  (imported from level_helpers so level files share them)
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import SAFE, WARN, ATCK
import level_megalovania
import level_bigshot

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
        'name':     'Megalovania',
        'subtitle': '120 BPM  \u00b7  40 s  \u00b7  1-beat warn',
        'bpm':      120,
        'music':    'Megalovania.ogg',
        'data':     level_megalovania.build_level(warn_beats=1),
    },
    {
        'name':     'Megalovania Easy Mode',
        'subtitle': '120 BPM  \u00b7  40 s  \u00b7  2-beat warn',
        'bpm':      120,
        'music':    'Megalovania.ogg',
        'data':     level_megalovania.build_level(warn_beats=2),
    },
    {
        'name':     '[[BIG SHOT]]',
        'subtitle': '140 BPM  \u00b7  40 s  \u00b7  1-beat warn',
        'bpm':      140,
        'music':    'BIGSHOT.ogg',
        'data':     level_bigshot.build_level(),
    },
]



# ═══════════════════════════════════════════════════════════════════════════
#  PLAYER
# ═══════════════════════════════════════════════════════════════════════════
class Player:
    def __init__(self):
        self.pos   = CENTER
        self.held  = []
        self.flash = 0
        self.glow  = 0

    def key_down(self, key):
        if key in KEY_POS and key not in self.held:
            self.held.append(key)
            self.pos = KEY_POS[key]

    def key_up(self, key):
        if key in self.held:
            self.held.remove(key)
            self.pos = KEY_POS[self.held[-1]] if self.held else CENTER

    def update(self, dt):
        self.flash = max(0, self.flash - dt)
        self.glow  = max(0, self.glow  - dt)

    @property
    def tint(self):
        if self.flash > 0: return C_PLR_HIT
        if self.glow  > 0: return C_PLR_DGD
        return C_PLR

    def draw(self, surf):
        r, c   = self.pos
        rect   = cell_rect(r, c)
        cx, cy = rect.centerx, rect.centery

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


def draw_grid(surf, grid, sprites, t_ms):
    for r in range(3):
        for c in range(3):
            rect  = cell_rect(r, c)
            state = grid[r][c]

            if state == SAFE:
                col = C_SAFE
            elif state == WARN:
                p   = (math.sin(t_ms * 0.013) + 1) * 0.5
                col = tuple(int(C_SAFE[i] + (C_WARN[i] - C_SAFE[i]) * p) for i in range(3))
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

        if (t // 500) % 2 == 0:
            blit_text(screen, "PRESS  ENTER  TO  START", F_MED, WHITE, SW//2, SH - 46)

        pygame.display.flip()


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

        screen.fill(BG)
        blit_text(screen, "SELECT  LEVEL", F_BIG, PURPLE, SW//2, 80)

        for i, lv in enumerate(LEVELS):
            y      = 200 + i * 98
            is_sel = (i == sel)
            bg     = (48, 38, 78) if is_sel else (22, 17, 38)
            rect   = pygame.Rect(SW//2 - 230, y - 28, 460, 64)
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
    level    = LEVELS[level_idx]
    data     = level['data']
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
                player.key_down(ev.key)
            if ev.type == pygame.KEYUP:
                player.key_up(ev.key)

        while seg_idx < len(data) and seg_timer >= data[seg_idx]['duration']:
            seg_timer -= data[seg_idx]['duration']
            seg_idx   += 1

        if seg_idx >= len(data):
            break

        cur     = data[seg_idx]
        grid    = cur['grid']
        sprites = cur['sprites']

        for r in range(3):
            for c in range(3):
                old, new = prev_grid[r][c], grid[r][c]
                if old != WARN and new == WARN:
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
        draw_grid(screen, grid, sprites, pulse_t)
        player.draw(screen)
        draw_hud(screen, score, elapsed, total_ms, streak)
        for p in popups: p.draw(screen)
        pygame.display.flip()

    if music_ok: pygame.mixer.music.stop()
    SND_END.play()
    return score, 'end'


# ═══════════════════════════════════════════════════════════════════════════
#  SCREEN: END
# ═══════════════════════════════════════════════════════════════════════════
def screen_end(score):
    t = 0

    for threshold, grade, gcol in [
        (2400, 'S', GOLD),
        (2000, 'A', GREEN),
        (1600, 'B', PURPLE),
        (800,  'C', WHITE),
        (0,    'D', RED),
    ]:
        if score >= threshold:
            break

    descs = {'S': '[[BIG SHOT]]!!!', 'A': 'You are filled with determination', 'B': 'NYEH HEH HEEEEH', 'C': '...', 'D': 'You ate the Moss'}

    while True:
        dt = clock.tick(FPS)
        t += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return 'quit'
            if ev.type == pygame.KEYDOWN: return 'menu'

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