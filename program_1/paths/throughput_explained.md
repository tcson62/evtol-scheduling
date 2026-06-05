# `throughput.py` — How it works

This script reads `next/start/arrival` facts from a `time-schedule.lp`-style
file, then emits `in/out` atoms that respect a throughput constraint of `k`
events per vertex per sliding window of length `w`.

Three stages: **parse** → **build legs** → **enforce**. Each is explained below.

---

## 1. Parsing — `parse_facts`

### One regex per predicate

```python
PAT_NEXT  = re.compile(r"^next\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)\s*\)\.")
PAT_START = re.compile(r"^start\(\s*(\d+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\.")
PAT_ARR   = re.compile(r"^arrival\(\s*(\d+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\.")
```

Two character classes do the work: `\d+` captures the integers (drone id,
sequence, time) and `\w+` captures vertex names (`lga`, `jfk`, …). `\s*`
between commas tolerates incidental whitespace. The `\.` at the end pins
to the trailing period so the line really is a fact.

### Line-by-line scan with a comment/blank skip

```python
for line in f:
    line = line.strip()
    if not line or line.startswith('%'):
        continue
```

`%` is ASP's comment syntax. Blank lines and comments are dropped.
Anything else gets tried against each pattern in turn — first match wins
and we `continue` so the same line isn't matched against another pattern.

### Capture order differs between predicates — that's the trap

The argument order is **not** the same:

| predicate              | arg 1 | arg 2 | arg 3 | arg 4 |
|------------------------|-------|-------|-------|-------|
| `next(d, s, v)`        | d     | s     | v     | —     |
| `start(d, v, s, t)`    | d     | v     | s     | t     |
| `arrival(d, v, s, t)`  | d     | v     | s     | t     |

So in `start` and `arrival`, the **third** regex group is the sequence
index and the **second** is the vertex. That's why the code looks "off":

```python
nexts[(int(m.group(1)), int(m.group(2)))] = m.group(3)
#       d,                s                =  v

starts[(int(m.group(1)), int(m.group(3)))] = (m.group(2), int(m.group(4)))
#        d,                s                  v,           t
```

### Why dicts keyed by `(drone, seq)`

`build_legs` later needs to ask "for drone d at sequence s, what was the
vertex / start time / arrival time?" Keying by `(d, s)` makes each lookup
O(1):

```python
nexts[(d, s)]      → v
starts[(d, s)]     → (v, t_dep)
arrivals[(d, s)]   → (v, t_arr)
```

Anything that doesn't match one of the three patterns (e.g. stray
`#show`, extra blank lines, unrelated atoms) is silently ignored.

---

## 2. Building legs — `build_legs`

`parse_facts` gives three lookup tables; `build_legs` walks them and
emits one record per actual flight.

```python
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
            legs.append({
                'drone':  d,
                'seq':    s_to,
                'v_from': v_from,
                'v_to':   v_to,
                't_out':  starts[(d, s_from)][1],
                't_in':   arrivals[(d, s_to)][1],
            })
    return legs
```

### Step 1 — group sequence indices by drone

```python
drone_seqs = defaultdict(list)
for (d, s) in nexts:
    drone_seqs[d].append(s)
for d in drone_seqs:
    drone_seqs[d].sort()
```

`nexts` is keyed by `(d, s)`. The first loop bins those keys per drone;
the second sorts each drone's sequence numbers ascending. After this,
`drone_seqs[0] == [0, 1, 2, …, 24]` etc.

`dict` iteration order has nothing to do with the path order — we have
to impose it explicitly.

### Step 2 — walk consecutive sequence pairs

```python
for i in range(len(seqs) - 1):
    s_from, s_to = seqs[i], seqs[i + 1]
```

A leg is the transition from one sequence index to the next. With sorted
seqs, `(s_from, s_to)` ranges over `(0,1), (1,2), …, (23,24)`. Two
`next/3` rows give us the leg's endpoints:

```python
v_from, v_to = nexts[(d, s_from)], nexts[(d, s_to)]
```

### Step 3 — skip the non-flights

```python
if v_from == v_to:
    continue
```

`next(d, 1, cri)` followed by `next(d, 2, cri)` means the drone stayed
at `cri`. There's no edge, no `in`/`out` atom, no contribution to vertex
throughput — drop it.

```python
if (d, s_from) not in starts or (d, s_to) not in arrivals:
    continue
```

A safety net: if either timing fact is missing (data gap, partial
input), skip rather than crash.

### Step 4 — emit the leg record

```python
legs.append({
    'drone':  d,
    'seq':    s_to,            # destination index — see below
    'v_from': v_from,
    'v_to':   v_to,
    't_out':  starts[(d, s_from)][1],   # departure from v_from
    't_in':   arrivals[(d, s_to)][1],   # arrival at v_to
})
```

Two things worth highlighting:

- `seq` is **`s_to`, not `s_from`**. That matches the atom convention:
  `out(d, (v,v'), s+1, t)` from `start(d, v, s, t)`, and
  `in(d, (v',v), s, t)` from `arrival(d, v, s, t)` — both atoms for the
  same flight carry the **destination's** sequence index. So one `s`
  per leg.
- `starts[...][1]` and `arrivals[...][1]` use index `[1]` because the
  dict stores `(vertex, time)` tuples; we already know the vertex from
  `nexts`, so we just need the time.

### Worked example — drone 0, first two legs

From `time-schedule.lp`:

```
next(0,0,lga).         next(0,1,cri).        next(0,2,cri).
start(0,lga,0,0).      start(0,cri,1,16).    start(0,cri,2,16).
                       arrival(0,cri,1,6).   arrival(0,cri,2,6).
```

The loop processes `(s_from=0, s_to=1)` and `(s_from=1, s_to=2)`:

| iter | s_from→s_to | v_from→v_to | same? | leg emitted |
|------|-------------|-------------|-------|-------------|
| 1    | 0 → 1       | lga → cri   | no    | `{drone:0, seq:1, v_from:lga, v_to:cri, t_out:0, t_in:6}` |
| 2    | 1 → 2       | cri → cri   | yes   | skipped |

Which prints back as `out(0,(lga,cri),1,0)` and `in(0,(lga,cri),1,6)`.

---

## 3. Enforcing the constraint — `enforce`

```python
def enforce(legs, k, w):
    by_drone = defaultdict(list)
    for L in legs:
        by_drone[L['drone']].append(L)
    for d in by_drone:
        by_drone[d].sort(key=lambda L: L['seq'])
    ...
```

### Step 1 — index legs by drone, sorted by sequence

We're about to mutate legs in place. Two access patterns will dominate,
so we set up indexes once:

- "Push drone D's leg s and every later leg forward by Δ" → needs the
  legs of drone D in seq order.
- "What's in window `[t, t+w]` at each vertex?" → built fresh each
  pass by `events_at_vertex`.

### Step 2 — the propagation helper

```python
def shift(drone, from_seq, delta):
    for L in by_drone[drone]:
        if L['seq'] >= from_seq:
            L['t_out'] += delta
            L['t_in'] += delta
```

The agreed rule: when one leg gets delayed by `delta`, **every** later
leg of the same drone slides by the same `delta`. Both `t_out` and
`t_in` of each affected leg shift, so flight times are preserved
exactly; only the ground time at the prior vertex absorbs the slack.
The mutation runs against the same dicts that `legs` holds — there's
no separate "scheduled" copy.

### Step 3 — the event index

```python
def events_at_vertex():
    ev = defaultdict(list)
    for L in legs:
        ev[L['v_from']].append((L['t_out'], L, 'out'))
        ev[L['v_to']].append((L['t_in'], L, 'in'))
    for v in ev:
        ev[v].sort(key=lambda x: (x[0], x[1]['drone'], x[1]['seq']))
    return ev
```

For each leg, the `out` atom lives at `v_from` (drone leaves there) and
the `in` atom lives at `v_to` (drone arrives there). After this call,
`ev[jfk]` is a time-sorted list of every event touching jfk, each
carrying back-pointers to the leg dict.

This is **rebuilt from scratch every pass** — after a shift, the old
list would be stale.

### Step 4 — the sweep

```python
t = 0
shifts = 0
while True:
    ev = events_at_vertex()
    if not ev: break
    max_time = max(e[0] for v in ev for e in ev[v])
    if t > max_time: break
    ...
```

Outer loop: a time cursor `t` starting at 0. The cursor only advances
when **every** vertex's window `[t, t+w]` is legal. Termination: shifts
only push events forward in time, and `max_time` grows by at most the
latest shift; once `t` exceeds it, nothing left to check.

### Step 5 — check + repair, one vertex per iteration

```python
violation = False
for v, events in ev.items():
    in_window = [e for e in events if t <= e[0] <= t + w]
    if len(in_window) > k:
        excess = len(in_window) - k
        for (_orig, L, kind) in in_window[-excess:]:
            cur = L['t_out'] if kind == 'out' else L['t_in']
            if cur > t + w:
                continue          # already moved by cascade
            delta = (t + w + 1) - cur
            if delta > 0:
                shift(L['drone'], L['seq'], delta)
                shifts += 1
        violation = True
        break
if not violation:
    t += 1
```

At each `t`, walk the vertices and find one whose window `[t, t+w]` has
more than `k` events. If we find one:

- `excess = len(in_window) - k` is how many we need to push out.
- `in_window[-excess:]` picks the **latest** events. They need the
  smallest delta to escape, so this realises "shift as little as
  possible" — both per atom and in total.
- For each chosen event, set its current time to `t + w + 1` (one minute
  past the window's end). The `if cur > t + w: continue` guard handles a
  subtle case: when two of the picked events belong to the same drone,
  the first `shift()` already cascades the second one forward, so by
  the time we get to it `cur` is already past the window — no further
  shift needed.
- After fixing, `break` and restart the outer loop at the **same `t`**
  — the rebuilt `ev` may now expose a new violation at a different
  vertex caused by the cascade.

If we made it through every vertex without firing, the window is clean
and we tick `t += 1`.

### Why "shift only forward" keeps it simple

Earlier windows (smaller `t`) only ever **lose** events as we sweep
forward — propagation never moves anything backward. So once a window
is legal we never have to revisit it; the algorithm is a one-pass
left-to-right sweep with restarts only at the current `t`.

### Details worth pinning down

A few questions tend to come up about exactly what `enforce` does. The
answers all fall out of the code in section 3.5, but it's worth stating
them explicitly.

**Q. When a window holds more than `k` atoms, are *all* excess atoms
shifted, or just one?**

All of them. The code computes `excess = len(in_window) - k` and walks
`in_window[-excess:]` — i.e., every atom past the cap, taking the
latest first because they need the smallest delta:

```python
excess = len(in_window) - k
for (_orig, L, kind) in in_window[-excess:]:
    ...
    delta = (t + w + 1) - cur
    if delta > 0:
        shift(L['drone'], L['seq'], delta)
```

Two follow-up subtleties:

1. **All excess atoms land on the same time `t+w+1`.** They aren't
   staggered. That can create a fresh violation at `t+w+1` (now `k+n`
   atoms stacked there), but the outer `while True` loop rebuilds the
   event index and revisits the window on the next iteration — the
   cascade keeps pushing forward until things settle.
2. **Cascade overlap is skipped.** Shifting the i-th excess atom moves
   every later leg of the same drone (`shift` propagates to all
   `seq >= from_seq`), so a subsequent excess atom in `in_window[-excess:]`
   may already sit past `t+w`. The `if cur > t + w: continue` guard
   prevents double-shifting it.

So the rule is: "shift exactly the excess count, all to `t+w+1`, modulo
cascade overlap" — and any secondary violation that creates is handled
on the next pass of the outer loop.

**Q. When an `in(d, (v',v), s, t)` atom needs to move because vertex
`v` is overloaded, what happens to the matching `out(d, (v',v), s, ·)`
atom at `v'`?**

It moves by the same delta. The two atoms belong to the **same leg
dict**, which carries both times:

```python
legs.append({
    'drone': d, 'seq': s,
    'v_from': v',  'v_to': v,
    't_out':  t_dep,    # departure from v'
    't_in':   t_arr,    # arrival at v
})
```

The vertex-event index built in `enforce` (section 3, step 3) points
both back at the same `L`:

```python
ev[L['v_from']].append((L['t_out'], L, 'out'))   # lives at v'
ev[L['v_to']].append(  (L['t_in'],  L, 'in'))    # lives at v
```

When a violation at `v` picks this leg's **in** event for shifting,
`shift(L['drone'], L['seq'], delta)` advances **both** `t_out` and
`t_in` of leg `L` by `delta` — so the out atom at `v'` moves in
lockstep with the in atom at `v`. The cascade then bumps every later
leg of the same drone by the same delta; the ground time at `v`
(between this in and the next leg's out) shrinks to absorb the shift.

The only asymmetry between the two kinds is which side determines
`delta`:

- in-event violation:  `delta = (t+w+1) - L['t_in']`
- out-event violation: `delta = (t+w+1) - L['t_out']`

After that, `shift` treats the leg as one unit.

**Q. So `t_in - t_out` (the flight time over edge `(v', v)`) stays
constant?**

Yes — by construction. `shift` adds the same `delta` to both `t_out`
and `t_in` of every affected leg, so `t_in - t_out` is invariant. The
only thing that changes is the **ground time at `v`** between this
leg's arrival and the next leg's departure. When the cascade pushes
leg `s` forward by `delta`, leg `s+1`'s `t_out` also moves by `delta`,
so the gap between them stays the same too — unless `polish` later
pulls leg `s+1` back, which is exactly the "ground time absorbs the
delay" step. `polish` only moves a leg's `t_out` (and `t_in` by the
same amount, lines 197-198), again preserving flight time, and it's
bounded below by the previous leg's `t_in` (lines 179-180), so it can
never overlap or shorten a flight.

### What `shifts` returns

The counter increments once per atom that the algorithm actively moved
(not once per cascaded leg). It's reported in the summary line:

```
enforce: applied 11688 forward shifts (k=5, w=15)  makespan 341 -> 809
```

The greedy enforce alone can blow makespan up significantly (here:
341 → 809). The next two sections describe two ways to reduce that
overshoot.

---

## 4. Pulling atoms back — `polish` (option c)

After `enforce` finishes, every leg satisfies the throughput constraint
but many have been pushed forward further than necessary. `polish` runs a
fixed-point sweep that pulls each leg back as far as it can go without
re-introducing a violation or breaking drone precedence.

```python
def polish(legs, k, w):
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
                ...
```

### Why two lower bounds

Every leg `L` of drone `d` at sequence `s` is bounded below by two
things:

1. **`orig_t_out`** — the input's departure time. Pulling below this
   would violate the original schedule's charge/flight constraints,
   which were tight by construction.
2. **`prev_in`** — the previous leg's *current* arrival time. After
   `enforce` has cascaded delays, the drone may now arrive at the
   pickup vertex later than originally; departing before that arrival
   is physically impossible.

`min_out = max(orig_t_out, prev_in)` captures both. The second bound is
the one that's easy to forget: without it, a polished leg could end up
*before* the drone arrived.

### Why a fixed-point loop

Pulling leg s back changes `prev_in` for leg s+1 (it stays the same or
gets smaller — `t_in` moves backward by however much we pulled `t_out`).
That may now allow leg s+1 to be pulled back further than it could before.
So one pass is not enough; we keep iterating until a full pass produces
no movement.

Within a single pass, the legs are processed **in seq order per drone**,
so leg s-1 is already at its minimum by the time we look at leg s.

### The throughput legality check

```python
def _is_legal(sorted_times, t_new, k, w):
    pos = bisect.bisect_left(sorted_times, t_new)
    merged = sorted_times[:pos] + [t_new] + sorted_times[pos:]
    for i in range(len(merged) - k):
        if merged[i + k] - merged[i] <= w:
            return False
    return True
```

The constraint "no window of length `w` contains more than `k` events"
is equivalent to:

> In the sorted list of event times, no group of `k+1` consecutive
> events spans `≤ w` minutes.

(If `k+1` events at times τ₁ ≤ … ≤ τ_{k+1} all sit within `w`, then the
window `[τ₁, τ₁+w]` contains all of them; conversely, any over-full
window's earliest `k+1` events form a span-`≤w` consecutive group in the
sorted list.)

So `_is_legal` inserts the proposed new time into the sorted list and
checks the (k+1)-event sliding window.

### Finding the minimum legal time

```python
new_out = None
for t in range(min_out, cur_out):
    if (_is_legal(others_from, t, k, w)
            and _is_legal(others_to, t + flight, k, w)):
        new_out = t
        break
```

Two vertices are involved per leg: the out atom at `v_from` and the in
atom at `v_to = v_from + flight`. The search scans `[min_out, cur_out)`
upward and picks the first `t` that is legal at **both** vertices. If
none is legal, the leg stays where it is.

### Result

`polish` reports back-shifts and the makespan delta:

```
enforce: applied 11688 forward shifts (k=5, w=15)  makespan 341 -> 809
polish : applied 948 back-shifts  makespan 809 -> 490
```

Polish recovered 319 minutes (~68% of enforce's overshoot) on this
input. Use `--no-polish` to disable the step and compare.

---

## 5. Absorbing delays into ground time — `throughput_absorb.py` (option b)

This is a second program (`throughput_absorb.py`) that imports
everything from `throughput.py` *except* `enforce`, and replaces it
with a version whose propagation rule is different.

### The two propagation rules

When `enforce` decides to delay leg s by Δ, it must update later legs
of the same drone. There are two natural rules:

**Uniform** (the rule from `throughput.py` / `throughput.lp`):

```
for L in by_drone[drone]:
    if L['seq'] >= from_seq:
        L['t_out'] += delta
        L['t_in'] += delta
```

Every later leg shifts by exactly Δ. All gaps (flight time *and* ground
time) are preserved exactly. Easy to reason about; pessimistic on
makespan.

**Absorb** (option b, in `throughput_absorb.py`):

```python
def shift(drone, from_seq, delta):
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
```

Walk forward through the drone's legs. For each next leg `L_curr`,
compute the minimum-legal departure given the new arrival time at the
previous vertex:

```
required_out = L_prev.t_in + min_ground
min_ground   = orig_t_out_curr - orig_t_in_prev    (the original gap)
```

If `L_curr` is already at or past `required_out`, the cascade
**stops** — the ground time soaked up the delay. Otherwise we shift
`L_curr` by exactly the residual, then check the next leg.

### When option (b) actually helps

On a drone's **first** delay, every later leg is at its original time
(no slack), so absorb degenerates into uniform: it has to push every
subsequent leg forward.

The benefit shows up on **second and later** delays to the same drone.
After the first cascade, every downstream leg sits at `orig + Δ₁`, i.e.,
has Δ₁ of slack. A subsequent delay of Δ₂ ≤ Δ₁ at an earlier seq can
now stop at the first downstream leg — its existing slack absorbs the
whole thing.

### Why both variants may produce identical output after polish

If `polish` is enabled (the default), it pulls every leg back to its
minimum. Whatever extra forward motion uniform did, polish undoes. The
two pipelines often **converge to the same makespan** after polish.

To see the difference clearly, disable polish:

```bash
python3 throughput.py        time-schedule.lp /tmp/u.lp -k 5 -w 15 --no-polish
python3 throughput_absorb.py time-schedule.lp /tmp/a.lp -k 5 -w 15 --no-polish
```

The post-enforce makespan and shift count from `throughput_absorb.py`
should be smaller (or equal, if no drone took a second delay). With
polish on, both lines may end at the same number — that's not a bug,
it's polish doing its job.

### Why the lower bounds in absorb are the same as in polish

Both rules respect the same precedence: leg s+1's departure cannot
precede leg s's current arrival plus the minimum original ground time.
This is also exactly what polish enforces when pulling back. So the
two operations are inverses: absorb is "push only the residual";
polish is "pull back to the same residual minimum." Combining them is
safe — neither can break the other's invariants.

---

## 6. Output retention on failure

Both `throughput.py` and `throughput_absorb.py` wrap the
enforce/polish/verify pipeline in `try: ... finally: write_output(...)`.
This means `<output.lp>` is always written from whatever state `legs`
has reached, even if an exception is raised partway through (e.g. by
`enforce`, `polish`, `verify`, or the optional plot step). The file is
retained rather than lost on a mid-run failure; on a successful run it
behaves exactly as before.

