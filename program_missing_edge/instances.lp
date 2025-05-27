vertiport(a;b;c).

drone(1;2;3).

init(1, a).
init(2, b).
init(3, c).


time(1..10).

max_time(FT) :- FT = #max{T:time(T)}.

edge((a, b)).
% edge((b, c)).
edge((c, a)).
edge((d, a)).
edge((e, b)).
edge((e, c)).

% customer(id, initloc, des)
customer(1, a, b).
customer(2, a, b).
customer(3, b, c).
customer(4, b, c).
customer(5, a, c).
customer(6, a, c).

customer(7, a, d).
customer(8, a, e).
customer(9, c, e).
customer(10, e, a).
customer(11, d, b).
customer(12, c, d).