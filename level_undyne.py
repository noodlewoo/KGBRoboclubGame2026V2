# ═══════════════════════════════════════════════════════════════════════════
#  A BATTLE AGAINST A TRUE HERO  –  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, attack, _safe_grid, _warn_grid, _hit_grid


def build_level():
    """
    150 BPM · 40 seconds · A Battle Against a True Hero.ogg

    Phase 1:  0– 6 s   single row or column attacks
    Phase 2:  6–18 s   two adjacent rows or two adjacent columns
                        (leaves exactly 1 safe row/column on the far side)
    Phase 3: 18–40 s   two adjacent rows/columns like phase 2, but each
                        attack is preceded by a fake warn showing a different
                        pair whose apparent safe spot is inside the real
                        attack's danger zone
    """
    BT    = round(60_000 / 150)   # 400 ms per beat @ 150 BPM
    W     = BT                     # 1-beat warn  (400 ms)
    H     = 200                    # hit duration
    TOTAL = W + BT                 # 800 ms per attack slot

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0,0),(0,1),(0,2)]   # row top
    RM = [(1,0),(1,1),(1,2)]   # row mid
    RB = [(2,0),(2,1),(2,2)]   # row bot
    CL = [(0,0),(1,0),(2,0)]   # col left
    CM = [(0,1),(1,1),(2,1)]   # col mid
    CR = [(0,2),(1,2),(2,2)]   # col right

    def u(*lines):
        seen = set(); out = []
        for line in lines:
            for c in line:
                if c not in seen: seen.add(c); out.append(c)
        return out

    def atk(*cells):
        return attack(TOTAL, *cells, warn_ms=W, hit_ms=H)

    segs = []
    add  = segs.extend

    # ── Phase 1: 0–6 s · single row or column ───────────────────────────────
    p1 = [RT, CL, RB, CR, RM, CM, RT]
    p1_n = 6_000 // TOTAL
    for i in range(min(p1_n, len(p1))):
        add(atk(*p1[i]))
    used = min(p1_n, len(p1)) * TOTAL
    if used < 6_000:
        segs.append(seg(6_000 - used, _safe_grid()))

    # ── Phase 2: 6–18 s · two adjacent rows or columns ──────────────────────
    # Each combo leaves exactly 1 safe row/column on the opposite side.
    #   u(RT,RM)  → safe: RB (bottom row)
    #   u(RM,RB)  → safe: RT (top row)
    #   u(CL,CM)  → safe: CR (right col)
    #   u(CM,CR)  → safe: CL (left col)
    p2 = [
        u(RT, RM),   # safe: RB
        u(CM, CR),   # safe: CL
        u(RM, RB),   # safe: RT
        u(CL, CM),   # safe: CR
        u(RT, RM),   # safe: RB
        u(CM, CR),   # safe: CL
        u(RM, RB),   # safe: RT
        u(CL, CM),   # safe: CR
        u(RT, RM),   # safe: RB
        u(CM, CR),   # safe: CL
        u(RM, RB),   # safe: RT
        u(CL, CM),   # safe: CR
        u(RT, RM),   # safe: RB
        u(CM, CR),   # safe: CL
        u(RM, RB),   # safe: RT
    ]
    p2_n = 12_000 // TOTAL
    for i in range(min(p2_n, len(p2))):
        add(atk(*p2[i]))
    used = min(p2_n, len(p2)) * TOTAL
    if used < 12_000:
        segs.append(seg(12_000 - used, _safe_grid()))

    # ── Phase 3: 18–40 s · fake-warn + adjacent row/col attacks ────────────
    # Each attack slot has THREE sub-phases:
    #   1. FAKE WARN  (1 beat) – warns a different adjacent pair; its apparent
    #                            safe spot is INSIDE the real attack's danger zone
    #   2. REAL WARN  (1 beat) – warns the actual pair that will hit
    #   3. HIT        (200 ms) + REST (200 ms)
    #
    # Fake/real pairs chosen so fake-safe ⊂ real-danger:
    #   real u(RT,RM) safe=RB → fake u(RM,RB) fake-safe=RT  (RT is in real ✓)
    #   real u(RM,RB) safe=RT → fake u(RT,RM) fake-safe=RB  (RB is in real ✓)
    #   real u(CL,CM) safe=CR → fake u(CM,CR) fake-safe=CL  (CL is in real ✓)
    #   real u(CM,CR) safe=CL → fake u(CL,CM) fake-safe=CR  (CR is in real ✓)
    W_FAKE  = BT          # 400 ms fake warn
    W_REAL  = BT          # 400 ms real warn
    H3      = 200
    REST3   = BT - H3     # 200 ms
    TOTAL3  = W_FAKE + W_REAL + H3 + REST3   # 1200 ms

    def fake_atk(fake_cells, real_cells):
        return [
            seg(W_FAKE, _warn_grid(*fake_cells)),
            seg(W_REAL, _warn_grid(*real_cells)),
            seg(H3,     _hit_grid(*real_cells)),
            seg(REST3,  _safe_grid()),
        ]

    p3_odd_patterns = [
        (u(RM, RB), u(RT, RM)),
        (u(CM, CR), u(CL, CM)),
        (u(RT, RM), u(RM, RB)),
        (u(CL, CM), u(CM, CR)),
    ]
    p3_even_patterns = [
        (u(CM, CR), u(RT, RM)),   # col fake, row real
        (u(RM, RB), u(CL, CM)),   # row fake, col real
        (u(CL, CM), u(RM, RB)),   # col fake, row real
        (u(RT, RM), u(CM, CR)),   # row fake, col real
    ]
    p3_n = 22_000 // TOTAL3      # 18 slots
    for i in range(p3_n):
        if i == 0:
            add(fake_atk((RB), u(RT, RM)))
        else:
            idx = i % 4
            patterns = p3_even_patterns if i % 2 == 0 else p3_odd_patterns
            fake_cells, real_cells = patterns[idx]
            add(fake_atk(fake_cells, real_cells))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
