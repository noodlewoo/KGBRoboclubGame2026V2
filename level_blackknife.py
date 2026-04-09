# ═══════════════════════════════════════════════════════════════════════════
#  BLACK KNIFE  –  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, _safe_grid, _warn_grid, _hit_grid, SAFE, WARN, ATCK


def build_level():
    """
    147.5 BPM · 40 seconds · BlackKnife.ogg

    Overlapping 1-beat-warn chain:
      Each attack warns for exactly 1 beat, then fires.
      The hit beat of attack N is the same segment as the warn beat of attack N+1.

    Segment layout for a chain of N attacks:
      [warn[0]] [hit[0]+warn[1]] [hit[1]+warn[2]] ... [hit[N-2]+warn[N-1]] [hit[N-1]]
    Duration = BT * N + H  (H = half-beat tail for final hit)

    Phase 1:  1–11 s   row cycling       (RT → RM → RB × 8,  24 attacks)
    Phase 2: 11–21 s   col cycling       (CL → CM → CR × 8,  24 attacks)
    Phase 3: 21–29 s   row + col mixed   ([RT,CL,RM,CM,RB,CR] × 3, 18 attacks)
    Phase 4: 29–36 s   diagonals woven in                          (16 attacks)
    Phase 5: 36–40 s   all-types finale                            (12 attacks)

    Total: 94 attacks · 94×407 + 203 = 38 461 ms attacks
           + 1 000 ms intro + ~539 ms safe tail = 40 000 ms
    """
    BT = round(60_000 / 147.5)   # 407 ms per beat @ 147.5 BPM
    H  = BT // 2                  # 203 ms half-beat final-hit tail

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0, 0), (0, 1), (0, 2)]   # row top
    RM = [(1, 0), (1, 1), (1, 2)]   # row mid
    RB = [(2, 0), (2, 1), (2, 2)]   # row bot
    CL = [(0, 0), (1, 0), (2, 0)]   # col left
    CM = [(0, 1), (1, 1), (2, 1)]   # col mid
    CR = [(0, 2), (1, 2), (2, 2)]   # col right
    D1 = [(0, 0), (1, 1), (2, 2)]   # diagonal TL→BR
    D2 = [(0, 2), (1, 1), (2, 0)]   # diagonal TR→BL

    def _combined(warn_cells, hit_cells):
        """Grid with hit_cells as ATCK and warn_cells as WARN (no clobbering)."""
        g = [SAFE] * 9
        for r, c in hit_cells:
            g[r * 3 + c] = ATCK
        for r, c in warn_cells:
            if g[r * 3 + c] == SAFE:
                g[r * 3 + c] = WARN
        return [g[0:3], g[3:6], g[6:9]]

    def chain(attacks):
        """Build overlapping 1-beat-warn chain from a list of cell groups."""
        if not attacks:
            return []
        result = [seg(BT, _warn_grid(*attacks[0]))]
        for i in range(len(attacks) - 1):
            result.append(seg(BT, _combined(attacks[i + 1], attacks[i])))
        result.append(seg(H, _hit_grid(*attacks[-1])))
        return result

    segs = []

    # ── Intro: 0–1 s ─────────────────────────────────────────────────────────
    segs.append(seg(1_000, _safe_grid()))

    # ── Full attack chain ─────────────────────────────────────────────────────
    attacks = (
        # Phase 1 – rows cycling (24 attacks)
        [RT, RM, RB] * 8 +

        # Phase 2 – cols cycling (24 attacks)
        [CL, CM, CR] * 8 +

        # Phase 3 – row + col interleaved (18 attacks)
        [RT, CL, RM, CM, RB, CR] * 3 +

        # Phase 4 – diagonals woven in with rows/cols (16 attacks)
        [D1, RT, D2, RM, CL, D1, D2, CM, D1, RB, D2, CR, D1, CM, D2, CL] +

        # Phase 5 – all-types finale (12 attacks)
        [D1, RT, D2, CL, D1, RM, D2, CR, D1, RB, D2, CM]
    )

    segs.extend(chain(attacks))

    # ── Pad to exactly 40 s ───────────────────────────────────────────────────
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
