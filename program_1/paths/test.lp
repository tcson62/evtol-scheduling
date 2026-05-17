time(1..266). 

#const max_seg=24. 

#const throughput=5. 

segment(0..max_seg).

moving(D, T):- segment(T), T > 0, 
    next(D, T-1, L'), next(D, T, L), L != L'.

bad(V, T, In + Out) :- time(T), vertiport(V), 
    In = #count{D : arrival(D, V, S, T'), T <= T', T' <= T+15, moving(D, S)}, 
    Out = #count{D : start(D, V, S, T'), T <= T', T' <= T+15, moving(D, S)}, 
    In + Out > throughput. 

inbad(arrival(D, jfk, S, T'), jfk, S, 1) :-  arrival(D, jfk, S, T'), 1 <= T', T' <= 16, moving(D, S).
inbad(start(D, jfk, S, T'), jfk, S, 1) :-   start(D, jfk, S, T'), 1 <= T', T' <= 16, moving(D, S).

#show inbad/4. 

% #show bad/3. 
