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
    148 BPM · 40 seconds · death by glamour 40sec.ogg

    Structure:
    M1-M4: slow intro
    M5-M8: complicates
    M9-M16: simplifies and escalates
    M17-M24: complicates


    warn_beats : 1 → 500 ms warn   (normal)
                 2 → 1000 ms warn  (easy mode)
    """
    BT    = round(6e4/(148))              # ms per beat @ 148 BPM, sixteenth notes
    W     = BT * warn_beats  # warn duration
    H     = 200              # hit duration
    TOTAL = W + BT           # slot = warn + 1 beat (hit 200 ms + rest 1 ms)

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

    # ── SINGLE PHASE: because the bpm sucks balls ────────────────
    all_attacks = [
        #1
        u(RM, RT),
        u(RT, RB),
        u(RM, RB),
        u(RT, RB),
        #1
        u(CM, CR),
        u(CL, CR),
        u(CM, CL),
        u(CL, CR),
        #3
        u(RM, RT),
        u(RT, RB),
        u(RM, RB),
        u(RT, RB),
        #4
        u(CM, CR),
        u(CL, CR),
        u(CM, CL),
        u(CL, CR),
        #5
        u(RM, CM, RT),
        u(RT, CL, CR, RB),
        u(RM, CM, RB),
        u(RT, CL, CR, RB),
        #6
        u(CM, RM, CR),
        u(CR, RT, RB, CL),
        u(CM, RM, CL),
        u(CR, RT, RB, CL),
        #7
        u(RM, CM, RT),
        u(RT, CL, CR, RB),
        u(RM, CM, RB),
        u(RT, CL, CR, RB),
        #8
        u(CM, RM, CR),
        u(CR, RT, RB, CL),
        u(CM, RM, CL),
        u(CR, RT, RB, CL),
        #9
        u(CM, CR, RM, RB),
        u(CM, CL, RM, RB),
        u(CM, CL, RM, RT),
        u(CM, CR, RM, RT),
        #10
        u(CL, CR, RM, RT),
        u(CM, CL, RT, RB),
        u(CR, CL, RB, RM),
        u(CM, CR, RB, RT),
        #11
        u(CM, CR, RM, RB),
        u(CM, CL, RM, RB),
        u(CM, CL, RM, RT),
        u(CM, CR, RM, RT),
        #12
        u(CL, CR, RM, RT),
        u(CM, CL, RT, RB),
        u(CR, CL, RB, RM),
        u(CM, CR, RB, RT),
        #13
        #14
        #15
        #16
        #17
        #18
        #19
        #20
        #21
        #22
        #23
        #24

    ]

    for attack_entry in all_attacks:
        if isinstance(attack_entry, tuple):
            cells, spr = attack_entry
            add(atk(*cells, spr=spr))
        else:
            add(atk(*attack_entry))

    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs