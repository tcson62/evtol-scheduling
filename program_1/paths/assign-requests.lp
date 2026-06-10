% %% clingo assign-requests.lp ti-shecudle-out-1.lp --out-ifs='\n' 

% #include "../instances/network_NY.lp".
% #include "../instances/init.lp".
% #include "../instances/rq.lp".

#include "../instances/network-ny_0_pax840_dirA2_dem3_init2_agent22_seg10_horizon180.lp".

% ----- TIME SCHEDULE WITH DIFFERENT CONSTRAINT
% start time at initial vertiport = charge duration

totalEdge(E, TF) :- edge(E), TF = #count{D, S, T : out(D, E, S, T)}. 

maxFlight((V, V'), R/C + 1) :- edge((V, V')), V!=V', initial_request(_, (V,V'), R), capacity(_, C).

diff(E, M - F)  :- edge(E), maxFlight(E, M), totalEdge(E, F). 

carry(D, E, Start, C) :- out(D, E, _, Start), capacity(_, C), diff(E, TF), TF > 0. 
carry(D, E, Start, C) :- out(D, E, _, Start), capacity(_, C), diff(E, 0), 
                            #count{D', S' : out(D', E, _, S'), Start < S' } > 0. 
carry(D, E, Start, R - C*(R/C)) :- out(D, E, _, Start), capacity(_, C), diff(E, 0), 
                            #count{D', S' : out(D', E, _, S'), Start < S' } = 0, 
                            initial_request(_, E, R). 

totalCarry(X) :- X = #sum{C, D, E, S : carry(D, E, S, C)}. 

totalOutofBound(X) :- X = #count{D, E, S, T : in(D, E, S, T)}. 

flyingTime(D, X) :- agent(D), X = #max{T : in(D, _, _, T)}.

emptyFlight(D, E, S, T) :- out(D, E, S, T), not carry(D, E, T, _).

time(1..180). 

feasible(V, T, In+Out) :- time(T), vertiport(V), 
                  In = #count{D, S : in(D, (V',V), S, T'), V'!=V, T <= T' <= T+15}, 
                  Out = #count{D, S : out(D, (V,V'), S, T'), V'!=V, T <= T' <= T+15}, 
                  In + Out < 5. 

maxServed((V,V'), M, R) :- edge((V,V')), flight_time((V,V'), FT), 
                        charge_time((V,V'), CT), V!=V',  N = 180/(FT+CT),
                        initial_request(_, (V,V'), R), 
                        capacity(_, C), M = N*C, R >= N*C.

maxServed((V,V'), R, R) :- edge((V,V')), flight_time((V,V'), FT), 
                        charge_time((V,V'), CT), V!=V',  N = 180/(FT+CT),
                        initial_request(_, (V,V'), R), 
                        capacity(_, C), R < N*C.

maxTotalServed(TS) :- TS = #sum{C, E : maxServed(E, C, _)}.  


#show.
#show maxServed/3.
#show maxTotalServed/1. 
#show totalEdge/2.
#show diff/2.
#show carry/4. 
#show flyingTime/2. 
#show totalCarry/1. 
#show totalOutofBound/1. 
#show emptyFlight/4.
#show display(in(D, (V, dandy), S, T)) : in(D, (V, dandy), S, T), T>=157, T<=172.   
#show display(out(D, (dandy, V), S, T)) : out(D, (dandy, V), S, T), T>=157, T<=172.   
#show display(in(D, (V, teb), S, T)) : in(D, (V, teb), S, T), T>=165.   
#show display(out(D, (teb, V), S, T)) : out(D, (teb, V), S, T), T>=165.   
#show feasible/3.  