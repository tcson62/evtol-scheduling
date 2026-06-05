#!/usr/bin/env python3
"""Throughput-constrained scheduler.

Reads facts of the form
    next(d, s, v).
    start(d, v, s, t).
    arrival(d, v, s, t).
and writes facts of the form
    out(d, (v, v'), s, t).
    in(d, (v', v), s, t).
such that for every vertex v and every window [t, t+w], the number of
in/out atoms at v with time in [t, t+w] is at most k.

For each consecutive pair of sequence indices (s-1, s) of a drone d with
v_from = next(d, s-1) != next(d, s) = v_to, we emit a leg with
    out atom: out(d, (v_from, v_to), s, t_dep)   t_dep = start(d, v_from, s-1, _)
    in  atom: in (d, (v_from, v_to), s, t_arr)   t_arr = arrival(d, v_to, s, _)

When a vertex window [t, t+w] holds more than k atoms, the latest atoms
in that window are pushed forward to t+w+1; the shift propagates to every
later leg of the same drone (flight times preserved, ground time at the
prior vertex absorbs the delay).

Usage:
    python throughput.py <input.lp> <output.lp> [-k 5] [-w 15]
"""
import argparse
import bisect
import re
from collections import defaultdict


PAT_NEXT = re.compile(r"^next\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)\s*\)\.")
PAT_START = re.compile(r"^start\(\s*(\d+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\.")
PAT_ARR = re.compile(r"^arrival\(\s*(\d+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\.")


def parse_facts(path):
    nexts, starts, arrivals = {}, {}, {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            m = PAT_NEXT.match(line)
            if m:
                nexts[(int(m.group(1)), int(m.group(2)))] = m.group(3)
                continue
            m = PAT_START.match(line)
            if m:
                starts[(int(m.group(1)), int(m.group(3)))] = (m.group(2), int(m.group(4)))
                continue
            m = PAT_ARR.match(line)
            if m:
                arrivals[(int(m.group(1)), int(m.group(3)))] = (m.group(2), int(m.group(4)))
    return nexts, starts, arrivals


def build_legs(nexts, starts, arrivals):
    drone_seqs = defaultdict(list)
    for (d, s) in nexts:
        drone_seqs[d].append(s)
    for d in drone_seqs:
        drone_seqs[d].sort()

    legs = []
    for d, seqs in drone_seqs.items():
        for i in range(len(seqs) - 1):
            s_from, s_to = seqs[i], seqs[i + 1]
            v_from, v_to = nexts[(d, s_from)], nexts[(d, s_to)]
            if v_from == v_to:
                continue
            if (d, s_from) not in starts or (d, s_to) not in arrivals:
                continue
            t_out = starts[(d, s_from)][1]
            t_in = arrivals[(d, s_to)][1]
            legs.append({
                'drone': d,
                'seq': s_to,
                'v_from': v_from,
                'v_to': v_to,
                't_out': t_out,
                't_in': t_in,
                'orig_t_out': t_out,   # lower bound for polish (charge/flight constraints)
                'orig_t_in': t_in,
            })
    return legs


def enforce(legs, k, w):
    by_drone = defaultdict(list)
    for L in legs:
        by_drone[L['drone']].append(L)
    for d in by_drone:
        by_drone[d].sort(key=lambda L: L['seq'])

    def shift(drone, from_seq, delta):
        for L in by_drone[drone]:
            if L['seq'] >= from_seq:
                L['t_out'] += delta
                L['t_in'] += delta

    def events_at_vertex():
        ev = defaultdict(list)
        for L in legs:
            ev[L['v_from']].append((L['t_out'], L, 'out'))
            ev[L['v_to']].append((L['t_in'], L, 'in'))
        for v in ev:
            ev[v].sort(key=lambda x: (x[0], x[1]['drone'], x[1]['seq']))
        return ev

    t = 0
    shifts = 0
    while True:
        ev = events_at_vertex()
        if not ev:
            break
        max_time = max(e[0] for v in ev for e in ev[v])
        if t > max_time:
            break
        violation = False
        for v, events in ev.items():
            in_window = [e for e in events if t <= e[0] <= t + w]
            if len(in_window) > k:
                excess = len(in_window) - k
                # shift the LATEST excess atoms (smallest delta each)
                for (_orig, L, kind) in in_window[-excess:]:
                    cur = L['t_out'] if kind == 'out' else L['t_in']
                    if cur > t + w:
                        continue  # already moved by cascade
                    delta = (t + w + 1) - cur
                    if delta > 0:
                        shift(L['drone'], L['seq'], delta)
                        shifts += 1
                violation = True
                break
        if not violation:
            t += 1
    return shifts


def _is_legal(sorted_times, t_new, k, w):
    """True if placing an event at t_new keeps the per-vertex window cap (k events
    in any window of length w) satisfied for the vertex whose other event times are
    in sorted_times. Equivalent check: in the merged sorted list, no k+1 consecutive
    entries have span ≤ w."""
    pos = bisect.bisect_left(sorted_times, t_new)
    merged = sorted_times[:pos] + [t_new] + sorted_times[pos:]
    for i in range(len(merged) - k):
        if merged[i + k] - merged[i] <= w:
            return False
    return True


def polish(legs, k, w):
    """Pull each leg back in time as far as possible without violating throughput
    or precedence. Lower bounds per leg:
      - t_out ≥ orig_t_out                       (charge/flight from the input)
      - t_out ≥ previous-leg.t_in (same drone)   (drone can't depart before it arrived)
    Iterates until no leg moves; returns the count of back-shifts applied."""
    by_drone = defaultdict(list)
    for L in legs:
        by_drone[L['drone']].append(L)
    for d in by_drone:
        by_drone[d].sort(key=lambda L: L['seq'])

    moves = 0
    while True:
        ev = defaultdict(list)
        for L in legs:
            ev[L['v_from']].append((L['t_out'], L, 'out'))
            ev[L['v_to']].append((L['t_in'], L, 'in'))

        any_moved = False
        for d, dlegs in by_drone.items():
            for i, L in enumerate(dlegs):
                cur_out = L['t_out']
                flight = L['t_in'] - L['t_out']
                prev_in = dlegs[i - 1]['t_in'] if i > 0 else 0
                min_out = max(L['orig_t_out'], prev_in)
                if min_out >= cur_out:
                    continue

                others_from = sorted(t for (t, L2, kind) in ev[L['v_from']]
                                     if not (L2 is L and kind == 'out'))
                others_to = sorted(t for (t, L2, kind) in ev[L['v_to']]
                                   if not (L2 is L and kind == 'in'))

                new_out = None
                for t in range(min_out, cur_out):
                    if (_is_legal(others_from, t, k, w)
                            and _is_legal(others_to, t + flight, k, w)):
                        new_out = t
                        break

                if new_out is not None:
                    L['t_out'] = new_out
                    L['t_in'] = new_out + flight
                    # Update in-place so legs processed later in this pass see the new time
                    for j, (_, L2, kind) in enumerate(ev[L['v_from']]):
                        if L2 is L and kind == 'out':
                            ev[L['v_from']][j] = (new_out, L, 'out')
                            break
                    for j, (_, L2, kind) in enumerate(ev[L['v_to']]):
                        if L2 is L and kind == 'in':
                            ev[L['v_to']][j] = (new_out + flight, L, 'in')
                            break
                    moves += 1
                    any_moved = True

        if not any_moved:
            break
    return moves


def makespan(legs):
    return max(L['t_in'] for L in legs) if legs else 0


def verify(legs, k, w):
    """Recompute the max window count at each vertex; return (ok, max_count)."""
    ev = defaultdict(list)
    for L in legs:
        ev[L['v_from']].append(L['t_out'])
        ev[L['v_to']].append(L['t_in'])
    worst = 0
    worst_v, worst_t = None, None
    for v, times in ev.items():
        times.sort()
        j = 0
        for i, ti in enumerate(times):
            while times[j] < ti - w:
                j += 1
            cnt = i - j + 1
            if cnt > worst:
                worst, worst_v, worst_t = cnt, v, ti
    return worst <= k, worst, worst_v, worst_t


def print_first_legs(legs, n=2, label=''):
    by_drone = defaultdict(list)
    for L in legs:
        by_drone[L['drone']].append(L)
    for d in by_drone:
        by_drone[d].sort(key=lambda L: L['seq'])
    if label:
        print(f"--- first {n} legs per drone ({label}) ---")
    else:
        print(f"--- first {n} legs per drone ---")
    for d in sorted(by_drone):
        for L in by_drone[d][:n]:
            print(f"  drone {d:>2} seq {L['seq']:>2}: "
                  f"out({d},({L['v_from']},{L['v_to']}),{L['seq']},{L['t_out']})  "
                  f"in({d},({L['v_from']},{L['v_to']}),{L['seq']},{L['t_in']})")


def display_vertex_schedule(legs, vertex, k, w, label=''):
    """Print every in/out event at `vertex` sorted by time.

    Each line shows the count of events in the forward window [t, t+w] and
    flags the row when that count exceeds k.
    """
    events = []
    for L in legs:
        if L['v_from'] == vertex:
            events.append((L['t_out'], L, 'out'))
        if L['v_to'] == vertex:
            events.append((L['t_in'], L, 'in'))
    events.sort(key=lambda x: (x[0], x[1]['drone'], x[1]['seq']))

    tag = f" ({label})" if label else ''
    print(f"--- schedule at vertex {vertex}{tag} ---")
    if not events:
        print("  (no events)")
        return

    times = [e[0] for e in events]
    for (t, L, kind) in events:
        cnt = sum(1 for tt in times if t <= tt <= t + w)
        flag = '  *VIOLATES*' if cnt > k else ''
        edge = f"({L['v_from']},{L['v_to']})"
        print(f"  t={t:>4}  {kind:<3}  drone {L['drone']:>2} seq {L['seq']:>2}  "
              f"edge {edge:<18}  win[{t},{t+w}]={cnt}{flag}")


def plot_vertex_schedule(legs_before, legs_after, vertex, k, w, save_path=None):
    """Two-panel before/after plot for `vertex`, saved to `save_path` as PNG.

    Top panel: in/out event markers + rolling window-count overlay.
    Bottom panel: same, after rescheduling.

    Requires matplotlib; if unavailable, prints a hint and returns without
    raising.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')   # headless backend; no display needed
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        print("[plot] matplotlib not installed — skipping plot. "
              "Install with: python3 -m pip install matplotlib")
        return

    def collect(legs, v):
        ins, outs = [], []
        for L in legs:
            if L['v_to'] == v:
                ins.append(L['t_in'])
            if L['v_from'] == v:
                outs.append(L['t_out'])
        return sorted(ins), sorted(outs)

    def rolling_counts(times, t_max, w):
        return [sum(1 for tt in times if t <= tt <= t + w) for t in range(t_max + 1)]

    ins_b, outs_b = collect(legs_before, vertex)
    ins_a, outs_a = collect(legs_after, vertex)
    all_times = ins_b + outs_b + ins_a + outs_a
    t_max = (max(all_times) if all_times else 0) + w + 5

    fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

    for ax, ins, outs, title in [
        (axes[0], ins_b, outs_b, f'vertex {vertex} — before'),
        (axes[1], ins_a, outs_a, f'vertex {vertex} — after'),
    ]:
        ax.scatter(ins, [1] * len(ins), marker='v', color='C0', s=50, zorder=3, label='in')
        ax.scatter(outs, [-1] * len(outs), marker='^', color='C1', s=50, zorder=3, label='out')
        ax.axhline(0, color='black', lw=0.5)
        ax.set_ylim(-2.5, 2.5)
        ax.set_yticks([-1, 1])
        ax.set_yticklabels(['out', 'in'])
        ax.set_title(title)
        ax.grid(True, axis='x', alpha=0.3)

        times = sorted(ins + outs)
        counts = rolling_counts(times, t_max, w)
        ax2 = ax.twinx()
        ax2.plot(range(t_max + 1), counts, color='gray', lw=1.2, alpha=0.8, label=f'count in [t, t+{w}]')
        ax2.axhline(k, color='red', ls='--', lw=1, alpha=0.7, label=f'cap k={k}')
        ax2.set_ylim(0, max(max(counts, default=0), k) + 2)
        ax2.set_ylabel('window count')

        # shade violating windows
        viol_x = [t for t, c in enumerate(counts) if c > k]
        for vx in viol_x:
            ax.axvspan(vx, vx + 1, color='red', alpha=0.08, zorder=0)

        handles_left, labels_left = ax.get_legend_handles_labels()
        handles_right, labels_right = ax2.get_legend_handles_labels()
        ax.legend(handles_left + handles_right + [Patch(facecolor='red', alpha=0.15, label='violation')],
                  labels_left + labels_right + ['violation'],
                  loc='upper right', fontsize=8)

    axes[1].set_xlabel('time (minutes)')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
        print(f"wrote {save_path}")
    plt.close(fig)


def write_output(legs, path):
    legs_sorted = sorted(legs, key=lambda L: (L['drone'], L['seq']))
    with open(path, 'w') as f:
        for L in legs_sorted:
            f.write(f"out({L['drone']},({L['v_from']},{L['v_to']}),{L['seq']},{L['t_out']}).\n")
            f.write(f"in({L['drone']},({L['v_from']},{L['v_to']}),{L['seq']},{L['t_in']}).\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('-k', type=int, default=5, help='throughput cap per vertex per window')
    p.add_argument('-w', type=int, default=15, help='window length')
    p.add_argument('--show-vertex', default=None,
                   help='vertex whose schedule to display before/after; '
                        'defaults to the worst-violating vertex in the input')
    p.add_argument('--plot', default=None, metavar='FILE',
                   help='also render a PNG before/after plot of --show-vertex to FILE')
    p.add_argument('--no-polish', action='store_true',
                   help='skip the back-shift polish pass (faster but worse makespan)')
    args = p.parse_args()

    nexts, starts, arrivals = parse_facts(args.input)
    legs = build_legs(nexts, starts, arrivals)
    print(f"parsed {len(legs)} legs from {args.input}")
    try:
        print_first_legs(legs, n=2, label='before')

        ok0, worst0, v0, t0 = verify(legs, args.k, args.w)
        print(f"before: max window count = {worst0} at vertex {v0} (end-of-window t={t0})")

        display_v = args.show_vertex or v0
        display_vertex_schedule(legs, display_v, args.k, args.w, label='before')

        legs_before = [dict(L) for L in legs]   # snapshot for the plot
        ms0 = makespan(legs)

        shifts = enforce(legs, args.k, args.w)
        ms1 = makespan(legs)
        print(f"enforce: applied {shifts} forward shifts (k={args.k}, w={args.w})  "
              f"makespan {ms0} -> {ms1}")

        if not args.no_polish:
            pulls = polish(legs, args.k, args.w)
            ms2 = makespan(legs)
            print(f"polish : applied {pulls} back-shifts  "
                  f"makespan {ms1} -> {ms2}")

        print_first_legs(legs, n=2, label='after')

        ok1, worst1, v1, t1 = verify(legs, args.k, args.w)
        status = 'OK' if ok1 else 'STILL VIOLATING'
        print(f"after : max window count = {worst1} [{status}]")
        display_vertex_schedule(legs, display_v, args.k, args.w, label='after')

        if args.plot:
            plot_vertex_schedule(legs_before, legs, display_v, args.k, args.w,
                                 save_path=args.plot)
    finally:
        write_output(legs, args.output)
        print(f"wrote {args.output}")


if __name__ == '__main__':
    main()
