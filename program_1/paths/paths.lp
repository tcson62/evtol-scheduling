%%% clingo paths.lp --out-ifs=\\n --outf=0 -V0 --out-atomf=%s. --quiet=1,2,2 > time.lp

#include "../instances/network_NY.lp".
#include "../instances/init.lp".
#include "../instances/rq.lp".

#const max_seg=24. 

#const throughput=5. 

#const cap=4. 

#const maxFlights=8. % upper bound of requests/cap 

segment(0..max_seg).

next(D, 0, L) :- init_loc(D, L). 

1 {next(D, T, L') :  edge((L, L'))} 1 :- segment(T), T > 0, next(D, T-1, L).

moving(D, T):- segment(T), T > 0, 
    next(D, T-1, L'), next(D, T, L), L != L'.

:- segment(T), T > 0, vertiport(L), 
    In = #count{D : next(D, T, L), moving(D, T)}, 
    Out = #count{D : next(D, T-1, L), moving(D, T-1)}, 
    In + Out > throughput.

:- edge((V, V')), V!=V', #count{D, T : segment(T), T > 0, next(D, T-1, V), next(D, T, V')} > maxFlights.

#show next/3. 











