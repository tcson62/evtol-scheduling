#include "../instances/network_NY.lp".
#include "../instances/init.lp".
#include "../instances/rq.lp".

% ----- TIME SCHEDULE WITH DIFFERENT CONSTRAINT
% start time at initial vertiport = charge duration

#const max_seg=24. 

#const throughput=5. 

segment(0..max_seg).

% flight(D, (L, L'), T-1) :- segment(T), T > 0, next(D, T-1, L), next(D, T, L'). 

% &diff {start(D,E,0) - 0} <= 0 :- flight(D, E, 0).

% &diff {start(D,E,X) - arrival(D,E,X)} <= -FT :- segment(X), flight_time(E,FT), flight(D,E,X).

% &diff {arrival(D,E,X) - start(D,E',X1)} <= -CT :- segment(X), charge_time(E',CT), flight(D,E,X), flight(D,E',X+1), X1=X+1.

&diff {start(D,L,0) - 0} <= 0 :- next(D, L, 0), D = #min{D' : next(D', L, 0)}.

&diff {start(D,E,X) - arrival(D,E,X)} <= -FT :- segment(X), flight_time(E,FT), flight(D,E,X).

&diff {arrival(D,E,X) - start(D,E',X1)} <= -CT :- segment(X), charge_time(E',CT), flight(D,E,X), flight(D,E',X+1), X1=X+1.
  