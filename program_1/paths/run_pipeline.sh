#!/usr/bin/env bash
#set -euo pipefail

prefix=$1

# echo 'compute PATHS' 

# 1. Generate paths
clingo paths.lp --out-ifs='\n' --outf=0 -V0 --out-atomf=%s. --quiet=1,2,2 > "$prefix"/time.lp

# echo 'remove SATISFIABLE' 

# 2. Remove the last line of time.lp
sed -i '' -e '$d' "$prefix"/time.lp

# echo 'compute NEXT' 

# 3. Assign next over the generated paths
clingo assign-next.lp "$prefix"/time.lp --out-ifs='\n' --outf=0 -V0 --out-atomf=%s. --quiet=1,2,2 > "$prefix"/time-schedule.lp

# echo 'remove SATISFIABLE 2' 

# 4. Remove the last line of time-schedule.lp
sed -i '' -e '$d' "$prefix"/time-schedule.lp

# echo 'run Throughpu' 

# 5. Run throughput
python3 throughput.py "$prefix"/time-schedule.lp "$prefix"/time-schedule-out.lp -k 5 -w 15

