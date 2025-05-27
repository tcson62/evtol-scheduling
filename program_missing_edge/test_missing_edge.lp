% #include "instances/instances.lp".

time(1..5).

max_time(FT) :- FT = #max{T:time(T)}.

cust_loc(C, L, 1) :- customer(C, L, _).
% create loop:
edge((X, X)) :- vertiport(X).
edge((X, Y)) :- edge((Y, X)), vertiport(X;Y).

% agent cap
cap(X, 4):- agent(X).

% planning
{as(D, (L, L1), 1):edge((L, L1))} = 1:- agent(D), init_loc(D, L).
{as(D, (L, L1), T):edge((L, L1))} = 1:- agent(D), time(T), as(D, (_, L), T-1).


% assign customer to flights
0 {ticket(D, C, (L, L1), T)} 1:- cust_loc(C, L, T), as(D, (L,L1), T).

change(C, T) :- ticket(_, C, _ ,T).


% update loc:
cust_loc(C, L1, T+1):- ticket(_, C, (L, L1), T).

cust_loc(C, L, T+1) :- not change(C, T), cust_loc(C, L, T), time(T).

% cannot have more than 1 ticket at a time
:- ticket(_, C, (L, _), T), ticket(_, C, (L1, _), T), L != L1.

% cannot have too many customer on agent at the same time
:- TC = #count{C:ticket(D, C, _, T)}, time(T), cap(D, MC), TC>MC.

% customer cannot be at 2 place at the same time
:- cust_loc(C, L1, T), cust_loc(C, L2, T), L1 != L2.

% custumer must be at loc at final time
:- customer(C, _, FD), cust_loc(C, L, FT), max_time(FT), L != FD.

% once reach destination, do not move anywhere else
:- cust_loc(C, L, T), cust_loc(C, L1, T+1), customer(C, _, L), L != L1.

#show as/3.
% #show ticket/3.
#show cust_loc/3.
% % #show changes/4.



