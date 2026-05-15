#include "instances/network_NY.lp".
#include "instances/init.lp".
#include "instances/rq.lp".

1 {as(D, (L',L), 0..C, T-1) } 1 :- next(D, T-1, L'), next(D, T, L), capacity(D,C).  

% total delivered customers can not excess demand
:- (R+1) #sum{W,D,X:as(D,E,W,X)}, edge(E), request(_,E,R).

:- as(_,(L,L),W,_), W > 0.

% penalty(D, E, S, 1) :- as(D, E, 0, S), not edge_loop(E).
% :~ penalty(D, _, S, P). [P, D, S]

%:- as(D,E,W,_), as(D',E,W',_), W>0, W'>0, D!=D', W+W'<4.


#heuristic as(_,_,W,_) : W > 0. [W,true]

#show as/4. 
#show next/3. 