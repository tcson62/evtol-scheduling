# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Answer Set Programming (ASP) based eVTOL fleet scheduling research code. Two largely independent programs explore different formulations of the same problem (routing aircraft over a vertiport network to serve passenger requests):

- **program_1/** — Revenue-maximization over a planning horizon (minutes). Requests are aggregated per edge (`request(N, (V,V'), R)`), and time is modeled via `clingo-dl` difference constraints (`&diff {arrival(...) - start(...)} = FT`). The objective explores revenue, profit, charging cost, emission cost, and empty-flight penalties.
- **program_2/** — Passenger-throughput maximization over discrete time steps. Requests are timestamped (`request(N, V, V', WR, T)`), and routing uses an aggregated edge-weight encoding (`edge_w(E, W, T)`, `node_w(V, W, T)`). Wraps Heulingo / LNPS (large-neighborhood prioritized search) for optimization.

The two programs do **not** share ASP files, instance formats, or Python utilities — treat them as separate codebases that happen to live in one repo.

## Requirements

- `clingo` and `clingo-dl` on PATH (program_1 needs `clingo-dl`; program_2 needs both).
- **program_1**: Python 3.9 specifically — the `clingodl` Python API only binds to 3.9. Plus `numpy`, `pandas`, `openpyxl` (for `MER_LMP_Information.xlsx`).
- **program_2**: Python 3.10. Heulingo lives at `program_2/lnps-solver/` and is invoked from the shell script.

## Common commands

### program_1 — schedule.lp (clingo-dl + heuristic)

Run directly with clingo-dl (instance files are `#include`-d from `schedule.lp`, so they must be regenerated first):

```bash
cd program_1
python instances/gen_init_random_NY.py <n_agents> <seed> <vertiport_cap>   # writes instances/init.lp
python instances/gen_rq_NY.py <customers_per_edge>                         # writes instances/rq.lp
clingo-dl schedule.lp -c start_seg=0 -c max_seg=11 -c horizon=180 --heuristic=Domain
```

Or via the Python wrapper, which also runs the post-processing (`compute_revenue.lp`, then `utils/sort_answer_set.py`) and writes to `results/`:

```bash
cd program_1
python solver.py --n_agents 10 --n_rq 10 --max_segment 10 --horizon 180 --time_limit 30
```

`solverClingoAPI.py` is an alternative entry point that uses the `clingodl` Python API directly (the `Schedule` class in that file) instead of shelling out to `clingo-dl`.

Key constants exposed via `-c`: `start_seg`, `max_seg`, `horizon`. Heuristic variants live in `opt_heu/` and additional optimization layers (e.g. `opt_heu/opt_1.lp`, `opt_heu/opt_2.1.lp`) can be appended to the `clingo-dl` invocation — see `run.txt` and `command_run.txt` for in-use combinations.

### program_2 — opt_lnps.lp via Heulingo

```bash
cd program_2
./solver_lnps.sh                # defaults: a=10 aircraft, t=6 steps, LNPS=True
./solver_lnps.sh a=40 t=11      # 40 aircraft, 11-step horizon
./solver_lnps.sh l=False        # bypass Heulingo, fall back to plain clingo
```

The script `#include`s `instance/{init,mer_lmp,network,rq}.lp` plus `opt_lnps.lp` and `compute_path.lp`. To test on a smaller request set, edit `solver_lnps.sh` to point at `instance/rq_small.lp` instead of `rq.lp`. Heulingo configuration parameters live in `lnps_config.lp`.

## Architecture notes that span files

### program_1 — what schedule.lp expects

`schedule.lp` is the entry point and is built on top of three included instance files that are *generated* (not hand-edited):

- `instances/network_NY.lp` — static: 7-vertiport NY graph (jfk, lga, teb, ryend, cri, cimbl, dandy), `edge/1`, `distance/2`, `flight_time/2`, `charge_time/2`.
- `instances/init.lp` — produced by `gen_init_random_NY.py`; declares `agent/1`, `capacity/2`, `init_loc/2`.
- `instances/rq.lp` — produced by `gen_rq_NY.py`; declares `request/3` aggregated per directed edge.

The core decision predicate is `as(D, E, W, X)` — agent `D` flies edge `E` carrying `W` passengers in segment index `X`. Time is layered on top via `clingo-dl` `&diff` atoms (`start/4`, `arrival/4`); these are currently commented out in `schedule.lp` because the active heuristic operates on segments only. Several optimization variants (penalize unserved customers, penalize empty flights, profit-maximization) exist as commented-out blocks inside `schedule.lp` — uncomment the chosen one rather than adding a parallel file.

Post-processing pipeline (driven by `solver.py`):
1. Capture `clingo-dl` stdout.
2. `utils/get_answer_set.py` extracts the last answer set into `results/result_answer_set.lp`.
3. `compute_revenue.lp` is run via plain `clingo` against the extracted answer set to derive revenue facts.
4. `utils/sort_answer_set.py` re-parses the output, joins against `MER_LMP_Information.xlsx` (the 7-row MER and LMP sheets, indexed in the same vertiport order as above), and produces revenue/profit/charging-cost/emission-cost totals plus the sorted human-readable output in `results/`.

Hard-coded constants worth knowing about when touching this pipeline:
- Velocity = 100 in `sort_answer_set.py` (used to convert distance → flight minutes).
- Battery model: `current_battery = 25`, charge factor `*24/25`, charging rate 250 kW (see lines around `data['charge_time']`).
- Distance matrix is duplicated as a hard-coded `numpy` array in `sort_answer_set.py` — must stay in sync with `network_NY.lp` if vertiports change.

### program_2 — opt_lnps.lp / compute_path.lp data flow

`compute_path.lp` generates the routing decisions: at each `time(0..total_steps)` it chooses an `edge_w((V,V'), W, T)` for outbound flow from each vertiport, with the conservation rule that `node_w(V, I, T)` is the sum of inbound `edge_w` values offset by edge travel time `distance_t(E, S)`. `opt_lnps.lp` then derives `revenue(N, R)` per request based on whether the flow on the request's edge at the request's time covers `WR` passengers, and minimizes `-R`.

Hyperparameters threaded through `-c` flags: `n` (used in `lnps_config.lp`), `total_steps`. Aircraft capacity, speed, and rate constants are `#const`s at the top of `compute_path.lp` (`speed=3` mile/min, `capacity=4`, `charging_rate=250`).

### Heulingo / LNPS solver

`program_2/lnps-solver/` is a third-party-style component (authored externally; `heulingo.py` header credits Irumi Sugimori). It plugs into clingo's `Application` interface and runs LNS over the optimization program. Treat it as a black box unless explicitly working on the search strategy — modify `lnps_config.lp` to tune neighborhood selection rather than editing the Python.

## Conventions and gotchas

- **Instance files are generated, not source.** Editing `program_1/instances/init.lp` or `rq.lp` by hand will be overwritten the next time `solver.py` runs. Modify the generator scripts (`gen_init_random_NY.py`, `gen_rq_NY.py`) instead.
- **`solver.py` must run from `program_1/`** — paths to `instances/`, `results/`, and `MER_LMP_Information.xlsx` are relative.
- **The `results/` directory must exist** before `solver.py` runs; the code writes into it without creating it.
- **No automated test suite exists.** Verification is done by reading the printed `revenue`/`profit`/`em_cost`/`chg_cost` totals at the end of a run and (optionally) the PDFs/SVGs produced by `program_1/visualize/visualize.py`.
- **`.lp` files in the repo root and stray ones under `program_1/`** (`tmp.lp`, `tv.lp`, `v.lp`, `s.lp`, `test_*.lp`, `output*.lp`, `solution.lp`) are scratch/intermediate output — not part of the encoding. Prefer not to depend on them.
