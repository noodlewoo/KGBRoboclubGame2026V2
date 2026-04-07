# ═══════════════════════════════════════════════════════════════════════════
#  LEVEL HELPERS  –  shared utilities imported by every level file
# ═══════════════════════════════════════════════════════════════════════════

# ── Square states ───────────────────────────────────────────────────────────
SAFE = 0   # all clear
WARN = 1   # attack incoming (warning / pre-flash)
ATCK = 2   # actively attacked

# ── Colors used by level builders ──────────────────────────────────────────
GOLD   = (255, 205,  50)
ORANGE = (255, 145,  40)
TEAL   = ( 70, 220, 200)
PURPLE = (215, 168, 255)

# ── Grid helpers ────────────────────────────────────────────────────────────
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

# ── Segment / attack builders ───────────────────────────────────────────────
def seg(dur, grid, sprites=None):
    return {'duration': dur, 'grid': grid, 'sprites': sprites or []}

def attack(total_ms, *cells, warn_ms=255, hit_ms=185, sprites=None):
    rest_ms = total_ms - warn_ms - hit_ms
    if rest_ms < 0:
        warn_ms = int(total_ms * 0.58)
        hit_ms  = total_ms - warn_ms
        rest_ms = 0
    sp  = sprites or []
    out = [
        seg(warn_ms, _warn_grid(*cells), sp),
        seg(hit_ms,  _hit_grid(*cells),  sp),
    ]
    if rest_ms > 0:
        out.append(seg(rest_ms, _safe_grid()))
    return out

# ── Sprite helpers ───────────────────────────────────────────────────────────
def mk_sprite(cells, color, label='', alpha=190):
    return {'cells': list(cells), 'color': color, 'label': label, 'alpha': alpha}

ARROWS = {
    'r': '→', 'l': '←', 'u': '↑', 'd': '↓',
    'ul': '↖', 'ur': '↗', 'dl': '↙', 'dr': '↘', 'x': '✕', 'o': '●',
}

def arrow_sp(cells, direction, color=GOLD):
    return mk_sprite(cells, color, ARROWS.get(direction, '?'), 215)
