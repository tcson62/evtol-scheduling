#include "../instances/network_NY.lp".
#include "../instances/init.lp".
#include "../instances/rq.lp".

% edge((V,V')) :- out(_,(V,V'),_,_).

numberOfFlights((V,V'), Out) :- 
    edge((V,V')), 
    Out = #count{D,T : out(D,(V,V'),_,T)}, Out > 8.

keep(out(D,(V,V'),S,T)) :- out(D,(V,V'),S,T), T < 180.
keep(in(D,(V,V'),S,T)) :- in(D,(V,V'),S,T), T < 180.

%%%  schedule_start(D, (L, L'), T+CT) for T >= arrival(D, L, S, T), next(D, S-1, L) 
%%%  schedule_arrival(D, (L, L'), T') =   


% 2 {
% arrival(D, L, T, Y); start(D, L, T, Y) 
% } :- segment(T), next(D, T-1, L), next(D, T, L),  
%      start(D, L, T-1, Y).

%%%%%%% checking for throughout 

%% maxArrival(M) :- M = #max{AT : arrival(_, _, _, AT)}.

% timeCheck(1..M) :-  M = #max{AT : arrival(_, _, _, AT)}.

% violate(T, V, Total) :- timeCheck(T), T>= 16, vertiport(V), 
%     In = #count{D : arrival(D, V, S, AT), moving(D, S), T-15 <= AT, AT <= T}, 
%     Out = #count{D : start(D, V, S, AT), moving(D, S), T-15 <= AT, AT <= T}, 
%     Total = In + Out, 
%     Total > 5. 

% in(arrival(D, jfk, S, AT)) :- arrival(D, jfk, S, AT), moving(D, S-1), AT <= 16, 1<= AT.      
% in(start(D, jfk, S, AT)) :- start(D, jfk, S, AT), moving(D, S-1), AT <= 16, 1<= AT.   

% timeLine(T, D, V, arrival) :- vertiport(V), arrival(D, V, _, T). 
% timeLine(T, D, V, start) :- vertiport(V), start(D, V, _, T). 
% %%%%%

% V1 xxxx5xxxx1xxxx5    x starts at z and breaks the constrants on line V1
%                       because start    .....  
%                       because arrival 
%                       because start & arrival 
%                       x starts at z and breaks the constrants on line V2 
% V2 xxxx5xxxx1xxxx5


%%% order(start(D, V)):- vertiport(V), start(D, V, _, T).



% #show. 
% #show in/1. 

% % start(D, L, T, Y + CT) :- segment(T), next(D, T-1, L), next(D, T, L'), charge_time((L, L'), CT), arrival(D, L, T-1, Y).

% % arrival(D, L, T, Y) :- segment(T), not moving(D, T), next(D, T-1, L), start(D, L, T-1, Y).

% % start(D, L, T, Y) :- segment(T), not moving(D, T), next(D, T-1, L), start(D, L, T-1, Y).

% % start(D, L', T+1, A + CT):- segment(T), T> 0, charge_time((L,L'),CT), flight(D,E',T), pt(arrival(D, E, T), A).

% flight(D, (L, L'), T-1) :- segment(T), T > 0, next(D, T-1, L), next(D, T, L'). 

% &diff {start(D,E,0) - 0} <= 0 :- flight(D, E, 0).

% &diff {start(D,E,X) - arrival(D,E,X)} <= -FT :- segment(X), flight_time(E,FT), flight(D,E,X).

% &diff {arrival(D,E,X) - start(D,E',X1)} <= -CT :- segment(X), charge_time(E',CT), flight(D,E,X), flight(D,E',X+1), X1=X+1.

% &diff {arrival(D,E,M)} <= horizon :- flight(D,E,M), max_seg(D,M).

% #const horizon=500. 
 

% #show bad/3. 
