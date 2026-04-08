# ═══════════════════════════════════════════════════════════════════════════
#  BLACK KNIFE  –  LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════
from level_helpers import seg, _safe_grid, _warn_grid, _hit_grid


def build_level():
    """
    147.5 BPM · 40 seconds · BlackKnife.ogg

    Timing: half-beat warn (203 ms) + half-beat hit (203 ms) = 1 attack per beat

    Phase 1:  1–25 s
      1A:  1– 6 s   single row attacks  (RT → RM → RB cycling)
      1B:  7–11 s   single col attacks  (CL → CM → CR cycling)
      1C: 12–19 s   2-row attacks       (RT+RM ↔ RM+RB alternating)
      1D: 19–24 s   2-col attacks       (CL+CM ↔ CM+CR alternating)
      1E: 24–26 s   brief break

    Phase 2: 26–40 s   (blank for now)
    """
    BT   = round(60_000 / 147.5)   # 407 ms per beat @ 147.5 BPM
    W    = BT // 2                  # 203 ms half-beat warn
    H    = BT // 2                  # 203 ms half-beat hit
    SLOT = W + H                    # 406 ms per attack (~1 beat)

    # ── Named lines ──────────────────────────────────────────────────────────
    RT = [(0, 0), (0, 1), (0, 2)]   # row top
    RM = [(1, 0), (1, 1), (1, 2)]   # row mid
    RB = [(2, 0), (2, 1), (2, 2)]   # row bot
    CL = [(0, 0), (1, 0), (2, 0)]   # col left
    CM = [(0, 1), (1, 1), (2, 1)]   # col mid
    CR = [(0, 2), (1, 2), (2, 2)]   # col right

    def atk(cells):
        return [
            seg(W, _warn_grid(*cells)),
            seg(H, _hit_grid(*cells)),
        ]

    def fill(total_ms, pattern):
        """Fill total_ms with repeating pattern of attack groups."""
        result = []
        elapsed = 0
        i = 0
        while elapsed + SLOT <= total_ms:
            result += atk(pattern[i % len(pattern)])
            elapsed += SLOT
            i += 1
        if elapsed < total_ms:
            result.append(seg(total_ms - elapsed, _safe_grid()))
        return result

    segs = []
    add  = segs.extend

    # ── Intro: 0–1 s ─────────────────────────────────────────────────────────
    segs.append(seg(1_000, _safe_grid()))

    # ── 1A: 1–6 s · single row attacks ──────────────────────────────────────
    add(fill(5_000, [RT, RM, RB]))

    # ── Gap: 6–7 s ───────────────────────────────────────────────────────────
    segs.append(seg(1_000, _safe_grid()))

    # ── 1B: 7–11 s · single col attacks ─────────────────────────────────────
    add(fill(4_000, [CL, CM, CR]))

    # ── Gap: 11–12 s ─────────────────────────────────────────────────────────
    segs.append(seg(1_000, _safe_grid()))

    # ── 1C: 12–19 s · single col attacks ────────────────────────────────────
    add(fill(7_000, [CL, CM, CR]))

    # ── 1D: 19–24 s · single row attacks ────────────────────────────────────
    add(fill(5_000, [RT, RM, RB]))

    # ── 1E: 24–26 s · brief break ────────────────────────────────────────────
    segs.append(seg(2_000, _safe_grid()))

    # ── Phase 2: 26–40 s · blank for now ────────────────────────────────────
    segs.append(seg(14_000, _safe_grid()))

    # Pad to exactly 40 s
    total = sum(s['duration'] for s in segs)
    if total < 40_000:
        segs.append(seg(40_000 - total, _safe_grid()))

    return segs
