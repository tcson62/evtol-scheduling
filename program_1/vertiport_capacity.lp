% Per-vertiport cap on total (arrivals + departures) across the horizon.
% Default cap is k_cap; override individual vertiports with cap_override/2 facts,
% e.g. cap_override(jfk, 8). Stationed (V,V) loops and the X=0 placement segment
% are not counted.

#const k_cap = 5.

#defined cap_override/2.

cap(V, K)     :- cap_override(V, K).
cap(V, k_cap) :- vertiport(V), not cap_override(V, _).

touch(D, X, V) :- as(D, (V, V'), _, X), V != V', X > 0.
touch(D, X, V) :- as(D, (V', V), _, X), V != V', X > 0.

:- cap(V, K), K + 1 #count{ D, X : touch(D, X, V) }.
