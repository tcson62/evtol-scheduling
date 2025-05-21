node(a;b;c).

drone(1;2;3).

init(1, a).
init(2, b).
init(3, c).
% init(4, c).
% init(5, c).

time(1..4).

max_time(FT) :- FT = #max{T:time(T)}.

edge((a, b)).
% edge((b, c)).
edge((c, a)).

% customer(id, initloc, des)
customer(1, a, b).
customer(2, a, b).
customer(3, b, c).
customer(4, b, c).
customer(5, a, c).
customer(6, a, c).

cust_loc(C, L, 1) :- customer(C, L, _).
% create loop:
edge((X, X)) :- node(X).
edge((X, Y)) :- edge((Y, X)), node(X;Y).

% drone cap
cap(X, 2):- drone(X).

% planning
{as(D, (L, L1), 1):edge((L, L1))} = 1:- drone(D), init(D, L).
{as(D, (L, L1), T):edge((L, L1))} = 1:- drone(D), time(T), as(D, (_, L), T-1).


% assign customer to flights
0 {ticket(D, C, (L, L1), T)} 1:- cust_loc(C, L, T), as(D, (L,L1), T).

change(C, T) :- ticket(_, C, _ ,T).


% update loc:
cust_loc(C, L1, T+1):- ticket(_, C, (L, L1), T).

cust_loc(C, L, T+1) :- not change(C, T), cust_loc(C, L, T), time(T).

% cannot have more than 1 ticket at a time
:- ticket(_, C, (L, _), T), ticket(_, C, (L1, _), T), L != L1.

% cannot have too many customer on drone at the same time
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



