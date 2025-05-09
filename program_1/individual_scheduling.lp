% ------ INSTANCES
#include "instances/network_NY.lp".
#include "instances/init.lp".
#include "instances/rq.lp".

% ------ GENERATE ROUTING
max_seg(D,max_seg):-agent(D).

% -- assign edge to each segment
1 {as(D,E,0..C,X):edge(E)} 1 :- agent(D), capacity(D,C), X=1..(max_seg), as(D-1,_,_,1..max_seg), D>0.

1 {as(D,E,0..C,X):edge(E)} 1 :- agent(D), capacity(D,C), X=1..(max_seg), D=0.

% total delivered customers can not excess demand
:- (R+1) #sum{W,D,X:as(D,E,W,X)}, edge(E), request(_,E,R).

:- 1 #sum{W,D,X:as(D,E,W,X)}, edge(E), not request(_,E,_).

% stationed aircraft does not carry customers
:- as(_,(V,V),W,_), W!=0.

% start vertiport as specicfied
:- init_loc(D,V), as(D,(V',_),_,0), V!=V'.

% consecutive trips need to be connected
:-as(D,(V,V1),_,X),as(D,(V2,V3),_,X+1),V1!=V2.

% -- HEURISTIC
% independent scheduling
#heuristic as(D,E,W,X):distance(E,S). [D*100 + W*S*(max_seg-X+1)/10,true]

% Prioritize scheduling higher-revenue flight
% #heuristic as(_,E,W,X):distance(E,S). [W*S,true]

% Prioritize scheduling higher-revenue flights earlier in the trajectory
% #heuristic as(_,E,W,X):distance(E,S). [W*S*(max_seg-X+1),true]




%  ----------------------------
% ----- TIME SCHEDULE WITH DIFFERENT CONSTRAINT
% start time at initial vertiport = charge duration
&diff {start(D,E,1)} = 0 :- as(D,E,_,1).

&diff {arrival(D,E,M)} <= horizon :- as(D,E,_,M), max_seg(D,M).

&diff {arrival(D,E,X) - start(D,E,X)} = FT :- flight_time(E,FT), as(D,E,_,X).

&diff {start(D,E',X+1) - arrival(D,E,X)} >= CT :- charge_time(E',CT), as(D,E,_,X), as(D,E',_,X+1).
%  ----------------------------
% ------ optimization_1: penalize unserved customers.

% remain_cust(E,N-P) :- request(_,E,N), P=#sum{W,D,X: as(D,E,W,X)}, N!=P.
% :~ remain_cust(E,P). [P@1, E]


% ------ optimization_2: penalize empty flights.

penalty(D, E, S, 1) :- as(D, E, 0, S).
:~ penalty(D, _, S, P). [P, D, S]

%  ----------------------------

% display
#show as/4.