# ═══════════════════════════════════════════════════════════════════════════
#  BONETROUSLE  –  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, _safe_grid, _warn_grid, _hit_grid


def build_level():
    """
    150 BPM · 40 seconds · Bonetrousle.ogg
    Difficulty: Easy

    Timing: 3-beat warn (1200 ms) + 2-beat hit (800 ms) = 2000 ms per slot
    18 attacks × 2000 ms = 36 000 ms  +  2 000 ms intro  +  ~2 000 ms pad

    Papyrus fight translated to the grid:
      Bone sweeps (horizontal) → single row attacks
      Bone pillars (vertical)  → single col attacks
      Special attack maze      → alternating row/col patterns

    Phase 1:  2–14 s   bone rain        – rows sweep down then back up
    Phase 2: 14–26 s   bone pillars     – cols sweep right then back left
    Phase 3: 26–38 s   special attack   – Papyrus alternates rows and cols
    """
    BT   = round(60_000 / 150)   # 400 ms per beat @ 150 BPM
    W    = BT * 3                  # 1200 ms  3-beat warn
    H    = BT * 2                  # 800 ms   2-beat hit
    SLOT = W + H                   # 2000 ms per attack

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0, 0), (0, 1), (0, 2)]   # row top
    RM = [(1, 0), (1, 1), (1, 2)]   # row mid
    RB = [(2, 0), (2, 1), (2, 2)]   # row bot
    CL = [(0, 0), (1, 0), (2, 0)]   # col left
    CM = [(0, 1), (1, 1), (2, 1)]   # col mid
    CR = [(0, 2), (1, 2), (2, 2)]   # col right

    def atk(line):
        return [seg(W, _warn_grid(*line)), seg(H, _hit_grid(*line))]

    segs = []

    # ── Intro: 0–2 s ─────────────────────────────────────────────────────────
    segs.append(seg(2_000, _safe_grid()))

    # ── Phase 1: 2–14 s · bone rain (rows) ───────────────────────────────────
    # Sweep top→mid→bot (bones raining down), then bot→mid→top (bones rising back)
    for line in [RT, RM, RB, RB, RM, RT]:
        segs.extend(atk(line))

    # ── Phase 2: 14–26 s · bone pillars (cols) ───────────────────────────────
    # Sweep left→mid→right (pillars marching right), then right→mid→left (back)
    for line in [CL, CM, CR, CR, CM, CL]:
        segs.extend(atk(line))

    # ── Phase 3: 26–38 s · special attack (alternating row / col) ────────────
    # Papyrus fires a row, then a col, weaving across the grid
    for line in [RT, CL, RB, CR, RM, CM]:
        segs.extend(atk(line))

    # ── Pad to exactly 40 s ───────────────────────────────────────────────────
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
