
#include "instances/network_NY.lp".
#include "instances/init.lp".
#include "instances/rq.lp".

#const max_seg=24. 

#const throughput=5. 

segment(0..max_seg).


moving(D, T):- segment(T), T > 0, 
    next(D, T-1, L'), next(D, T, L), L != L'.

in(L, T, In):- segment(T), T > 0, vertiport(L), 
    In = #count{D : next(D, T, L), moving(D, T)}.

out(L, T, Out):- segment(T), T > 0, vertiport(L), 
    Out = #count{D : next(D, T-1, L), moving(D, T-1)}.

total(L, T, In + Out):- segment(T), T > 0, vertiport(L),   
    in(L, T, In), out(L, T, Out).


