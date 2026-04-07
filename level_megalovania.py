# ═══════════════════════════════════════════════════════════════════════════
#  MEGALOVANIA LEVEL BUILDER  (shared by both Megalovania entries)
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import (
    GOLD, ORANGE, TEAL, PURPLE,
    seg, attack, mk_sprite,
    _safe_grid,
)


def build_level(warn_beats):
    """
    120 BPM · 40 seconds · Megalovania.ogg

    Structure:
      0 – 15 s  single-line attacks (rows, columns, diagonals)
     15 – 40 s  combined-line attacks, nearly all hitting center

    warn_beats : 1 → 500 ms warn   (normal)
                 2 → 1000 ms warn  (easy mode)
    """
    BT    = 500              # ms per beat @ 120 BPM
    W     = BT * warn_beats  # warn duration
    H     = 200              # hit duration
    TOTAL = W + BT           # slot = warn + 1 beat (hit 200 ms + rest 300 ms)

    # ── Named lines ─────────────────────────────────────────────────────────
    RT = [(0,0),(0,1),(0,2)]   # row top
    RM = [(1,0),(1,1),(1,2)]   # row mid
    RB = [(2,0),(2,1),(2,2)]   # row bot
    CL = [(0,0),(1,0),(2,0)]   # col left
    CM = [(0,1),(1,1),(2,1)]   # col mid
    CR = [(0,2),(1,2),(2,2)]   # col right
    DM = [(0,0),(1,1),(2,2)]   # diagonal  ↘
    DA = [(0,2),(1,1),(2,0)]   # anti-diag ↙

    def u(*lines):
        """Union of cell lists in first-seen order."""
        seen = set(); out = []
        for line in lines:
            for c in line:
                if c not in seen: seen.add(c); out.append(c)
        return out

    def sp(cells, label, color=GOLD):
        return [mk_sprite(cells, color, label, 185)]

    def atk(*cells, spr=None):
        return attack(TOTAL, *cells, warn_ms=W, hit_ms=H, sprites=spr)

    segs = []
    add  = segs.extend

    # ── PHASE 1: single-line attacks  (0 – 15 s) ────────────────────────────
    # slots available: 15 000 // TOTAL  → 15 @ 1-beat warn, 10 @ 2-beat warn
    p1_n = 15_000 // TOTAL
    p1 = [
        (RT, sp(RT, '→')),
        (RB, sp(RB, '→')),
        (CL, sp(CL, '↓')),
        (CR, sp(CR, '↓')),
        (RM, sp(RM, '→', TEAL)),
        (CM, sp(CM, '↓', TEAL)),
        (DM, sp(DM, '↘', ORANGE)),
        (DA, sp(DA, '↙', ORANGE)),
        (RT, sp(RT, '→', PURPLE)),
        (RB, sp(RB, '→', PURPLE)),
        (CL, sp(CL, '↓', PURPLE)),
        (CR, sp(CR, '↓', PURPLE)),
        (DM, sp(DM, '↘', TEAL)),
        (DA, sp(DA, '↙', TEAL)),
        (RM, sp(RM, '→')),
    ]
    for cells, spr in p1[:p1_n]:
        add(atk(*cells, spr=spr))
    used = p1_n * TOTAL
    if used < 15_000:
        segs.append(seg(15_000 - used, _safe_grid()))

    # ── PHASE 2a: combined-line ramp-up  (15 – 25 s) ────────────────────────
    # All but the first attack hit center (1,1).  3+ safe squares allowed.
    p2a = [
        u(RT, RB),
        u(DM, DA),
        u(DM, DA, RT),
        u(DM, DA, RB),
        u(RT, RM),
        u(DM, DA, CL),
        u(DM, DA, CR),
        u(RT, RB, CM),
        u(CL, CR, RM),
        u(DM, DA, CM),
    ]
    p2a_n = 10_000 // TOTAL
    for cells in p2a[:p2a_n]:
        add(atk(*cells))
    used = p2a_n * TOTAL
    if used < 10_000:
        segs.append(seg(10_000 - used, _safe_grid()))

    # ── PHASE 2b: high-intensity  (25 – 40 s) ───────────────────────────────
    # All attacks hit center.  Only 1–2 safe squares, always corners or sides.
    p2b = [
        u(RT, RB, CM),
        u(CL, CR, RM),
        u(DM, DA, CM),
        u(RT, RB, DM),
        u(DM, DA, RT, CL),
        u(DM, DA, RB, CR),
        u(DM, DA, RT, CR),
        u(DM, DA, RB, CL),
        u(RT, RB, CM, CR),
        u(RT, RB, CM, CL),
        u(RB, RM, CL, CR),
        u(RT, RM, CL, CR),
        u(RB, RM, CR, CM),
        u(RB, RM, CL, CM),
        u(RT, RM, CR, CM),
        u(RT, RM, CL, CM),
    ]
    p2b_n = 15_000 // TOTAL
    for cells in p2b[:p2b_n]:
        add(atk(*cells))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
