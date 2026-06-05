#include "../instances/network_NY.lp".
#include "../instances/init.lp".
#include "../instances/rq.lp".

% ----- TIME SCHEDULE WITH DIFFERENT CONSTRAINT
% start time at initial vertiport = charge duration

#const max_seg=24. 

#const throughput=5. 

segment(0..max_seg).

moving(D, T-1):- segment(T), T > 0, 
    next(D, T-1, L'), next(D, T, L), L != L'.

% D starts at L in segment T at time X  

start(D, L, 0, 0)   :- next(D, 0, L). 

2 {
arrival(D, L', T, Y + FT); start(D, L', T, Y + FT + CT) 
} :- segment(T), T > 0, next(D, T-1, L), next(D, T, L'), %L != L', 
    flight_time((L, L'),FT), charge_time((L, L'), CT), start(D, L, T-1, Y).

#show.

#show arrival/4.
#show start/4.
#show next/3.
