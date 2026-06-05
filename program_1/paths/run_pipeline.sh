#!/usr/bin/env bash
set -euo pipefail

# 1. Generate paths
clingo paths.lp --out-ifs='\n' --outf=0 -V0 --out-atomf=%s. --quiet=1,2,2 > time.lp

# 2. Remove the last line of time.lp
sed -i '' -e '$d' time.lp

# 3. Assign next over the generated paths
clingo assign-next.lp time.lp --out-ifs='\n' --outf=0 -V0 --out-atomf=%s. --quiet=1,2,2 > time-schedule.lp

# 4. Remove the last line of time-schedule.lp
sed -i '' -e '$d' time-schedule.lp

# 5. Run throughput
python3 throughput.py time-schedule.lp time-schedule-out.lp -k 5 -w 15
