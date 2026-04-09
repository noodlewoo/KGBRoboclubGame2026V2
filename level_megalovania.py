# ═══════════════════════════════════════════════════════════════════════════
#  MEGALOVANIA LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, attack, _safe_grid, _warn_grid, _hit_grid


def build_level(warn_beats=1):
    """
    120 BPM · 40 seconds · Megalovania.ogg

    Phase 1  ( 0–15 s):
      – First 4 attacks: single center lines in each direction
          (center row, top-right diagonal, center col, top-left diagonal)
      – Remaining slots: alternating row+col cross and diagonal cross

    Phase 2a (15–25 s):
      – Alternates between a cross attack and a 2-adjacent-row/col attack

    Phase 2b (25–40 s):
      – Two sweeps (clockwise then counterclockwise).
        Each sweep: all 8 WARN frames back-to-back (safe cell rotates around
        the edge), then all 8 HIT frames back-to-back.
        Only 1 edge cell is safe at a time; all other 8 squares are danger.
    """
    BT    = 500              # ms per beat @ 120 BPM
    W     = BT * warn_beats  # warn duration
    H     = 200              # hit duration
    TOTAL = W + BT           # attack slot duration

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0,0),(0,1),(0,2)]   # row top
    RM = [(1,0),(1,1),(1,2)]   # row mid
    RB = [(2,0),(2,1),(2,2)]   # row bot
    CL = [(0,0),(1,0),(2,0)]   # col left
    CM = [(0,1),(1,1),(2,1)]   # col mid
    CR = [(0,2),(1,2),(2,2)]   # col right
    DM = [(0,0),(1,1),(2,2)]   # diagonal top-left  ↘
    DA = [(0,2),(1,1),(2,0)]   # diagonal top-right ↙

    ALL9 = [(r, c) for r in range(3) for c in range(3)]

    def u(*lines):
        seen = set(); out = []
        for line in lines:
            for cell in line:
                if cell not in seen: seen.add(cell); out.append(cell)
        return out

    def atk(*cells):
        return attack(TOTAL, *cells, warn_ms=W, hit_ms=H)

    segs = []
    add  = segs.extend

    # ── PHASE 1: 0–15 s ──────────────────────────────────────────────────────
    single_4   = [RM, DA, CM, DM]
    cross_pair = [u(RM, CM), u(DM, DA)]   # alternates after the single 4

    p1_n = 15_000 // TOTAL
    for i in range(p1_n):
        if i < 4:
            add(atk(*single_4[i]))
        else:
            add(atk(*cross_pair[(i - 4) % 2]))

    used = p1_n * TOTAL
    if used < 15_000:
        segs.append(seg(15_000 - used, _safe_grid()))

    # ── PHASE 2a: 15–25 s ────────────────────────────────────────────────────
    # Even indices → cross attack (alternates between the two cross types)
    # Odd  indices → adjacent pair (cycles through the four combos)
    p2a_crosses  = [u(RM, CM), u(DM, DA)]
    p2a_adjacent = [u(RT, RM), u(CL, CM), u(RM, RB), u(CM, CR)]

    p2a_n = 10_000 // TOTAL
    cross_i = adj_i = 0
    for i in range(p2a_n):
        if i % 2 == 0:
            add(atk(*p2a_crosses[cross_i % 2]))
            cross_i += 1
        else:
            add(atk(*p2a_adjacent[adj_i % 4]))
            adj_i += 1

    used = p2a_n * TOTAL
    if used < 10_000:
        segs.append(seg(10_000 - used, _safe_grid()))

    # ── PHASE 2b: 25–40 s · single clockwise spiral ──────────────────────────
    # 8 steps around the edge. All 8 WARN frames play first so the player can
    # read the full rotation, then all 8 HIT frames follow.
    # WARN_DUR = HIT_DUR, computed to fill exactly the remaining time.
    #   spiral_ms = 8×WARN + 8×(HIT+REST)  →  D = (spiral_ms - 8×REST) / 16

    REST_DUR  = 200
    spiral_ms = 40_000 - sum(s['duration'] for s in segs)
    D         = (spiral_ms - 8 * REST_DUR) // 16
    WARN_DUR  = D
    HIT_DUR   = D

    CW = [(2,1),(2,2),(1,2),(0,2),(0,1),(0,0),(1,0),(2,0)]  # clockwise

    def sweep(safe_order):
        result = []
        n = len(safe_order)
        # Each step: two consecutive edge cells are safe
        safe_pairs = [(safe_order[i], safe_order[(i + 1) % n]) for i in range(n)]
        # All warns first
        for pair in safe_pairs:
            danger = [c for c in ALL9 if c not in pair]
            result.append(seg(WARN_DUR, _warn_grid(*danger)))
        # All hits after
        for pair in safe_pairs:
            danger = [c for c in ALL9 if c not in pair]
            result.append(seg(HIT_DUR,  _hit_grid(*danger)))
            result.append(seg(REST_DUR, _safe_grid()))
        return result

    add(sweep(CW))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
