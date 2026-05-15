#include "instances/network_NY.lp".
#include "instances/init.lp".
#include "instances/rq.lp".

#const max_seg=24. 

#const throughput=10. 

segment(0..max_seg).

next(D, 0, L) :- init_loc(D, L). 

1 {next(D, T, L') :  edge((L, L'))} 1 :- segment(T), T > 0, next(D, T-1, L).

:- segment(T), T > 0, vertiport(L), 
    In = #count{D : next(D, T, L)}, 
    Out = #count{D : next(D, T-1, L), next(D, T, L'), edge((L, L')), L != L'}, 
    In + Out > throughput.

at(S, L) :- vertiport(L), S = #count{D : init_loc(D, L)}. 

#show next/3. 
#show at/2. 
#show as/4.











