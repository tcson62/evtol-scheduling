#include "../instances/network_NY.lp".
#include "../instances/init.lp".
#include "../instances/rq.lp".

% ----- TIME SCHEDULE WITH DIFFERENT CONSTRAINT
% start time at initial vertiport = charge duration

#const max_seg=24. 

#const throughput=5. 

segment(0..max_seg).

moving(D, T):- segment(T), T > 0, 
    next(D, T-1, L'), next(D, T, L), L != L'.

% start(D, L, 0, 0)   :- next(D, 0, L). 

% 2 {
% arrival(D, L', T, Y + FT); start(D, L', T, Y + FT + CT) 
% } :- segment(T), next(D, T-1, L), next(D, T, L'), 
%     flight_time((L, L'),FT), charge_time((L, L'), CT), start(D, L, T-1, Y).

% start(D, L, T, Y + CT) :- segment(T), next(D, T-1, L), next(D, T, L'), charge_time((L, L'), CT), arrival(D, L, T-1, Y).

% arrival(D, L, T, Y) :- segment(T), not moving(D, T), next(D, T-1, L), start(D, L, T-1, Y).

% start(D, L, T, Y) :- segment(T), not moving(D, T), next(D, T-1, L), start(D, L, T-1, Y).

% start(D, L', T+1, A + CT):- segment(T), T> 0, charge_time((L,L'),CT), flight(D,E',T), pt(arrival(D, E, T), A).

flight(D, (L, L'), T-1) :- segment(T), T > 0, next(D, T-1, L), next(D, T, L'). 

&diff {start(D,E,0) - 0} <= 0 :- flight(D, E, 0).

&diff {start(D,E,X) - arrival(D,E,X)} <= -FT :- segment(X), flight_time(E,FT), flight(D,E,X).

&diff {arrival(D,E,X) - start(D,E',X1)} <= -CT :- segment(X), charge_time(E',CT), flight(D,E,X), flight(D,E',X+1), X1=X+1.

% &diff {arrival(D,E,M)} <= horizon :- flight(D,E,M), max_seg(D,M).

% #const horizon=500. 
 