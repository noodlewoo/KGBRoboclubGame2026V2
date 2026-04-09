# ═══════════════════════════════════════════════════════════════════════════
#  BIG SHOT LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, attack, _safe_grid


def build_level():
    """
    140 BPM · 40 seconds · BIGSHOT.ogg
    Mainly random individual squares, warn = 1 beat.
    Every other attack hits the center block (1,1) at minimum.

    Phase 0:  0– 7 s  intro  (2 cells)
    Phase 1:  7–14 s  easy  (3 cells)      ← difficulty amp
    Phase 2: 14–21 s  medium (5 cells)     ← difficulty amp
    Phase 3: 21–27 s  hard  (6 cells)      ← difficulty amp
    Phase 4: 27–40 s  intense (7–8 cells)  ← difficulty amp
    """
    BT    = round(60_000 / 140)   # 429 ms per beat @ 140 BPM
    W     = 2 * BT                 # 2-beat warn
    H     = 200
    TOTAL = W + BT                 # 3 beats per slot (~1286 ms)

    def atk(*cells):
        return attack(TOTAL, *cells, warn_ms=W, hit_ms=H)

    segs = []
    add  = segs.extend

    # ── Phase 0: 0–7 s · 2-cell intro ──────────────────────────────────────
    p0 = [
        [(0,0),(2,2)],       # no center
        [(0,2),(1,1)],       # center
        [(0,1),(2,1)],       # no center
        [(1,1),(1,2)],       # center
        [(2,0),(0,2)],       # no center
        [(1,1),(0,0)],       # center
        [(2,2),(1,0)],       # no center
        [(1,1),(2,0)],       # center
    ]
    p0_n = 7_000 // TOTAL
    for i in range(min(p0_n, len(p0))):
        add(atk(*p0[i]))
    used = min(p0_n, len(p0)) * TOTAL
    if used < 7_000:
        segs.append(seg(7_000 - used, _safe_grid()))

    # ── Phase 1: 7–14 s · 3-cell random squares ─────────────────────────────
    p1 = [
        [(0,0),(1,2),(2,1)],       # no center
        [(0,2),(1,1),(2,0)],       # center
        [(0,1),(1,2),(2,0)],       # no center
        [(0,0),(1,1),(2,2)],       # center
        [(2,0),(2,2),(0,1)],       # no center
        [(0,1),(1,1),(2,2)],       # center
        [(0,2),(2,0),(2,1)],       # no center
        [(0,0),(1,1),(1,2)],       # center
        [(1,0),(0,2),(2,2)],       # no center
        [(0,2),(1,1),(2,1)],       # center
        [(0,2),(1,0),(2,0)],       # no center
        [(0,1),(1,1),(2,0)],       # center
        [(0,0),(0,1),(2,2)],       # no center
        [(1,1),(2,1),(2,0)],       # center
        [(1,0),(0,1),(2,2)],       # no center
        [(0,0),(1,1),(2,0)],       # center
    ]
    p1_n = 7_000 // TOTAL
    for i in range(min(p1_n, len(p1))):
        add(atk(*p1[i]))
    used = min(p1_n, len(p1)) * TOTAL
    if used < 7_000:
        segs.append(seg(7_000 - used, _safe_grid()))

    # ── Phase 2: 14–21 s · 5-cell random squares ────────────────────────────
    p2 = [
        [(0,0),(0,2),(1,1),(2,0),(2,2)],       # center
        [(0,1),(1,0),(1,2),(2,0),(2,2)],       # no center
        [(0,0),(0,1),(1,1),(2,1),(2,2)],       # center
        [(0,2),(1,0),(1,2),(2,0),(2,2)],       # no center
        [(0,0),(0,2),(1,1),(2,1),(2,2)],       # center
        [(0,1),(0,2),(1,0),(2,0),(2,1)],       # no center
        [(0,0),(1,1),(1,2),(2,0),(2,2)],       # center
        [(0,0),(0,2),(1,0),(2,1),(2,2)],       # no center
    ]
    p2_n = 7_000 // TOTAL
    for i in range(min(p2_n, len(p2))):
        add(atk(*p2[i]))
    used = min(p2_n, len(p2)) * TOTAL
    if used < 7_000:
        segs.append(seg(7_000 - used, _safe_grid()))

    # ── Phase 3: 21–27 s · 6-cell random squares ────────────────────────────
    p3 = [
        [(0,0),(0,1),(0,2),(1,1),(2,0),(2,2)],       # center
        [(0,0),(0,1),(0,2),(1,0),(2,0),(2,2)],       # no center
        [(0,0),(0,2),(1,1),(1,2),(2,0),(2,1)],       # center
        [(0,1),(0,2),(1,0),(1,2),(2,0),(2,2)],       # no center
        [(0,0),(0,2),(1,0),(1,1),(2,1),(2,2)],       # center
        [(0,0),(0,1),(1,2),(2,0),(2,1),(2,2)],       # no center
        [(0,0),(0,2),(1,1),(2,0),(2,1),(2,2)],       # center
    ]
    p3_n = 6_000 // TOTAL
    for i in range(min(p3_n, len(p3))):
        add(atk(*p3[i]))
    used = min(p3_n, len(p3)) * TOTAL
    if used < 6_000:
        segs.append(seg(6_000 - used, _safe_grid()))

    # ── Phase 4: 27–40 s · 7–8-cell intense random squares ──────────────────
    p4 = [
        [(0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,2)],          # 7 – center
        [(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,2)],          # 7 – no center
        [(0,0),(0,2),(1,0),(1,1),(1,2),(2,0),(2,2)],          # 7 – center
        [(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)],          # 7 – no center
        [(0,0),(0,1),(0,2),(1,1),(2,0),(2,1),(2,2)],          # 7 – center
        [(0,0),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)],          # 7 – no center
        [(0,0),(0,1),(1,1),(1,2),(2,0),(2,1),(2,2)],          # 7 – center
        [(0,0),(0,1),(0,2),(1,0),(1,2),(2,1),(2,2)],          # 7 – no center
        [(0,0),(0,2),(1,0),(1,1),(1,2),(2,1),(2,2)],          # 7 – center
        [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,2)],    # 8 – center, safe (2,1)
        [(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)],    # 8 – no center, safe (1,1)
        [(0,0),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],    # 8 – center, safe (0,1)
        [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,1),(2,2)],    # 8 – center, safe (2,0)
        [(0,0),(0,1),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],    # 8 – center, safe (0,2)
        [(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],    # 8 – center, safe (0,0)
    ]
    p4_n = 13_000 // TOTAL
    for i in range(min(p4_n, len(p4))):
        add(atk(*p4[i]))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
