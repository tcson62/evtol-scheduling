#!/usr/bin/env python3
"""Compute prj_standard_tp-style metrics for a prj_paths schedule.

Reads out/in atoms produced by throughput.py:
    out(d,(v_from,v_to),s,t).   % a DEPARTURE at v_from  at time t
    in (d,(v_from,v_to),s,t).   % an ARRIVAL   at v_to    at time t

and reports the same throughput statistic as prj_standard_tp/stat_sch.lp:
fixed, non-overlapping 15-min windows per vertiport, counting arrivals +
departures (P = I + O); a window FAILS when P > vertiport_throughput.

Usage:
    python metrics.py time-schedule-out.lp [--throughput 5] [--window 15]
                                           [--horizon 180]
"""
import argparse
import re
from collections import defaultdict

PAT = re.compile(r"^(out|in)\((\d+),\((\w+),(\w+)\),(\d+),(\d+)\)\.")


def parse(path):
    """Return list of (vertex, time, kind) events. out->departure at v_from,
    in->arrival at v_to."""
    events = []
    flights = 0
    drones, vertices = set(), set()
    served_legs = []
    with open(path) as f:
        for line in f:
            m = PAT.match(line.strip())
            if not m:
                continue
            kind, d, v_from, v_to, _s, t = m.groups()
            d, t = int(d), int(t)
            drones.add(d)
            if kind == 'out':
                events.append((v_from, t, 'O'))
                vertices.add(v_from)
                flights += 1            # one leg == one out atom
                served_legs.append((d, (v_from, v_to)))
            else:
                events.append((v_to, t, 'I'))
                vertices.add(v_to)
    return events, flights, drones, vertices, served_legs


# ---- instance facts (distance, demand, seat capacity) for revenue metrics ----
PAT_DIST = re.compile(r"^distance\(\(\s*(\w+)\s*,\s*(\w+)\s*\),\s*(\d+)\)")
PAT_REQ = re.compile(
    r"^initial_request\(\s*\d+\s*,\s*\(\s*(\w+)\s*,\s*(\w+)\s*\),\s*(\d+)\)")
PAT_CAP = re.compile(r"^capacity\(\s*(\d+)\s*,\s*(\d+)\)")


def parse_instance(path):
    """Return (distance[(o,d)], demand[(o,d)], capacity[agent]) from an instance."""
    dist, cap = {}, {}
    demand = defaultdict(int)
    with open(path) as f:
        for line in f:
            line = line.strip()
            m = PAT_DIST.match(line)
            if m:
                dist[(m.group(1), m.group(2))] = int(m.group(3))
                continue
            m = PAT_REQ.match(line)
            if m:
                o, d, p = m.group(1), m.group(2), int(m.group(3))
                if o != d:
                    demand[(o, d)] += p
                continue
            m = PAT_CAP.match(line)
            if m:
                cap[int(m.group(1))] = int(m.group(2))
    return dist, demand, cap


def revenue_metrics(served_legs, dist, demand, cap):
    """Allocate passengers to served legs (up to each flight's seat capacity,
    bounded by remaining edge demand) and return revenue (passenger-miles),
    passengers served, and normalized yields. Mirrors prj_standard_tp's model:
    revenue = sum_edge distance(edge) * min(demand(edge), seats on that edge)."""
    seats_on_edge = defaultdict(int)
    for d, e in served_legs:
        seats_on_edge[e] += cap.get(d, 4)

    total_demand = sum(demand.values())
    max_revenue = sum(dist.get(e, 0) * p for e, p in demand.items())

    revenue = served = 0
    for e, dem in demand.items():
        carried = min(dem, seats_on_edge.get(e, 0))
        served += carried
        revenue += dist.get(e, 0) * carried

    yield_pct = (100.0 * revenue / max_revenue) if max_revenue else 0.0
    served_pct = (100.0 * served / total_demand) if total_demand else 0.0
    return {
        'revenue': revenue,
        'profit': revenue,          # profit == revenue until costs enter the model
        'passengers_served': served,
        'total_demand': total_demand,
        'max_revenue': max_revenue,
        'yield_pct': yield_pct,
        'served_pct': served_pct,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('schedule')
    ap.add_argument('--throughput', type=int, default=5)
    ap.add_argument('--window', type=int, default=15)
    ap.add_argument('--horizon', type=int, default=180)
    ap.add_argument('--instance', default=None,
                    help='instance .lp file; enables revenue/passenger metrics')
    ap.add_argument('-v', '--verbose', action='store_true',
                    help='list every failing (vertex, window) bin')
    args = ap.parse_args()

    events, flights, drones, vertices, served_legs = parse(args.schedule)
    if not events:
        print(f"no out/in atoms found in {args.schedule}")
        return

    makespan = max(t for _, t, _ in events)
    w = args.window
    n_windows = makespan // w + 1

    # throughput(P, V, W): arrivals + departures at V in fixed bin [W*w, (W+1)*w)
    bins = defaultdict(int)             # (vertex, window) -> P
    for v, t, _ in events:
        bins[(v, t // w)] += 1

    worst = max(bins.values())
    fails = {(v, W): p for (v, W), p in bins.items() if p > args.throughput}
    fail_count = len(fails)
    horizon_overflow = makespan - args.horizon

    print(f"=== metrics for {args.schedule} ===")
    print(f"drones (agents)      : {len(drones)}")
    print(f"flights (legs)       : {flights}")
    print(f"vertiports used      : {len(vertices)}")
    print(f"makespan             : {makespan} min")
    print(f"horizon              : {args.horizon} min"
          + (f"   *** OVER by {horizon_overflow} ***" if horizon_overflow > 0 else "   (within)"))
    print(f"throughput cap (k)   : {args.throughput}  per {w}-min fixed window")
    print(f"windows analyzed     : {n_windows}  (0..{makespan})")
    print(f"max window load (P)  : {worst}")
    print(f"failing bins         : {fail_count}"
          + ("  -> FAIL" if fail_count else "  -> PASS (all <= k)"))

    if args.verbose and fails:
        print("--- failing (vertiport, window, P) ---")
        for (v, W), p in sorted(fails.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {v:<8} win {W:>2} [{W*w:>4},{(W+1)*w:>4})  P={p}")

    if args.instance:
        dist, demand, cap = parse_instance(args.instance)
        rm = revenue_metrics(served_legs, dist, demand, cap)
        print("--- revenue / passenger metrics (prj_standard_tp model) ---")
        print(f"revenue (pax-miles)  : {rm['revenue']}")
        print(f"profit               : {rm['profit']}")
        print(f"passengers_served    : {rm['passengers_served']}  of {rm['total_demand']} demand")
        print(f"max_revenue          : {rm['max_revenue']}")
        print(f"yield_pct            : {rm['yield_pct']:.1f}%  (revenue / max_revenue)")
        print(f"served_pct           : {rm['served_pct']:.1f}%  (pax served / demand)")


if __name__ == '__main__':
    main()
