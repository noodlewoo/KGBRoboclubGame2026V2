# ═══════════════════════════════════════════════════════════════════════════
#  HIS THEME  –  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, _safe_grid, _warn_grid, _hit_grid


def build_level():
    """
    153 BPM · 40 seconds · HisTheme.ogg

    Timing: 2-beat warn (784 ms), 2-beat hit (784 ms) @ 153 BPM

    Phase 1:  0–10 s   single row/column sweeps of 3 in a direction
                        warn→hit immediately chain, no rest between attacks
    Phase 2: 10–40 s   3 warns then 3 attacks in direction
                        (rows going up/down or cols going right/left)
                        each hit followed by a 1-beat rest
    """
    BT = round(60_000 / 153)   # 392 ms per beat @ 153 BPM
    W  = BT * 2                 # 2-beat warn = 784 ms
    H  = BT * 2                 # 2-beat hit  = 784 ms

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0, 0), (0, 1), (0, 2)]   # row top
    RM = [(1, 0), (1, 1), (1, 2)]   # row mid
    RB = [(2, 0), (2, 1), (2, 2)]   # row bot
    CL = [(0, 0), (1, 0), (2, 0)]   # col left
    CM = [(0, 1), (1, 1), (2, 1)]   # col mid
    CR = [(0, 2), (1, 2), (2, 2)]   # col right

    segs = []
    add  = segs.extend

    # ── Phase 1: 0–10 s · single-line sweeps ────────────────────────────────
    # Each attack: warn (2bt) → hit (2bt), no rest — next warn follows immediately
    # SLOT = W + H = 784 + 784 = 1568 ms
    # 6 attacks × 1568 ms = 9408 ms + 592 ms pad = 10 000 ms

    SLOT = W + H

    def single_atk(line):
        return [
            seg(W, _warn_grid(*line)),
            seg(H, _hit_grid(*line)),
        ]

    # Two directional sweeps of 3:
    #   sweep 1: top→mid→bot (going down)
    #   sweep 2: left→mid→right (going right)
    p1_sweeps = [
        [RT, RM, RB],   # going down
        [CL, CM, CR],   # going right
    ]

    p1_time = 0
    for sweep in p1_sweeps:
        for line in sweep:
            add(single_atk(line))
            p1_time += SLOT

    if p1_time < 10_000:
        segs.append(seg(10_000 - p1_time, _safe_grid()))

    # ── Phase 2: 10–40 s · 3 warns then 3 attacks ───────────────────────────
    # Each sweep: warn×3 then (hit + 1-beat rest)×3
    # Duration: 3×784 + 3×(784 + 392) = 2352 + 3528 = 5880 ms
    # 5 sweeps × 5880 ms = 29 400 ms + 600 ms pad = 30 000 ms

    def sweep_pattern(lines):
        result = []
        for line in lines:
            result.append(seg(W, _warn_grid(*line)))
        for line in lines:
            result.append(seg(H,  _hit_grid(*line)))
            result.append(seg(BT, _safe_grid()))
        return result

    # Alternating directional sweeps for phase 2
    p2_sequences = [
        [RT, RM, RB],   # rows going down
        [CL, CM, CR],   # cols going right
        [RB, RM, RT],   # rows going up
        [CR, CM, CL],   # cols going left
        [RT, RM, RB],   # rows going down
    ]

    for seq in p2_sequences:
        add(sweep_pattern(seq))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
