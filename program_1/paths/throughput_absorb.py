#!/usr/bin/env python3
"""Throughput-constrained scheduler — ABSORB cascade variant (option b).

Same input/output and workflow as throughput.py, but the enforce step uses
a different propagation rule. When a leg is delayed by Δ, we walk forward
through the drone's legs and shift each subsequent leg only by what its
ground time cannot absorb; we stop as soon as a leg has enough slack.

Compared to the uniform cascade in throughput.py, this typically yields a
much smaller makespan blow-up before polish, because previously-introduced
slack (ground time above its original/minimum value) can soak up later
delays instead of pushing the whole drone tail forward.

Usage:
    python throughput_absorb.py <input.lp> <output.lp> [-k 5] [-w 15]
                                [--show-vertex jfk] [--plot file.png]
                                [--no-polish]
"""
import argparse
from collections import defaultdict

from throughput import (
    parse_facts, build_legs, polish, verify, makespan,
    print_first_legs, display_vertex_schedule, plot_vertex_schedule,
    write_output,
)


def enforce_absorb(legs, k, w):
    """Greedy sweep with absorb-style propagation."""
    by_drone = defaultdict(list)
    for L in legs:
        by_drone[L['drone']].append(L)
    for d in by_drone:
        by_drone[d].sort(key=lambda L: L['seq'])

    def shift(drone, from_seq, delta):
        """Delay leg `from_seq` by `delta`; cascade only into legs whose
        ground time can't absorb the residual delay."""
        dlegs = by_drone[drone]
        idx = next((i for i, L in enumerate(dlegs) if L['seq'] == from_seq), None)
        if idx is None:
            return
        dlegs[idx]['t_out'] += delta
        dlegs[idx]['t_in'] += delta
        for i in range(idx + 1, len(dlegs)):
            L_curr = dlegs[i]
            L_prev = dlegs[i - 1]
            min_ground = L_curr['orig_t_out'] - L_prev['orig_t_in']
            required_out = L_prev['t_in'] + min_ground
            if L_curr['t_out'] >= required_out:
                return       # ground-time slack absorbed the rest
            extra = required_out - L_curr['t_out']
            L_curr['t_out'] += extra
            L_curr['t_in'] += extra

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
                for (_orig, L, kind) in in_window[-excess:]:
                    cur = L['t_out'] if kind == 'out' else L['t_in']
                    if cur > t + w:
                        continue
                    delta = (t + w + 1) - cur
                    if delta > 0:
                        shift(L['drone'], L['seq'], delta)
                        shifts += 1
                violation = True
                break
        if not violation:
            t += 1
    return shifts


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('-k', type=int, default=5)
    p.add_argument('-w', type=int, default=15)
    p.add_argument('--show-vertex', default=None,
                   help='vertex whose schedule to display before/after; '
                        'defaults to the worst-violating vertex in the input')
    p.add_argument('--plot', default=None, metavar='FILE',
                   help='save a PNG before/after plot of --show-vertex to FILE')
    p.add_argument('--no-polish', action='store_true',
                   help='skip the back-shift polish pass')
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

        legs_before = [dict(L) for L in legs]
        ms0 = makespan(legs)

        shifts = enforce_absorb(legs, args.k, args.w)
        ms1 = makespan(legs)
        print(f"enforce[absorb]: applied {shifts} forward shifts "
              f"(k={args.k}, w={args.w})  makespan {ms0} -> {ms1}")

        if not args.no_polish:
            pulls = polish(legs, args.k, args.w)
            ms2 = makespan(legs)
            print(f"polish         : applied {pulls} back-shifts  "
                  f"makespan {ms1} -> {ms2}")

        print_first_legs(legs, n=2, label='after')

        ok1, worst1, v1, t1 = verify(legs, args.k, args.w)
        status = 'OK' if ok1 else 'STILL VIOLATING'
        print(f"after : max window count = {worst1} [{status}]")
        display_vertex_schedule(legs, display_v, args.k, args.w, label='after')

        if args.plot:
            plot_vertex_schedule(legs_before, legs, display_v, args.k, args.w,
                                 save_path=args.plot, show=False)
    finally:
        write_output(legs, args.output)
        print(f"wrote {args.output}")


if __name__ == '__main__':
    main()
