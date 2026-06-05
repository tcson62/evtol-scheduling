% Idea for throughput 

Given 

drone 0 : (v^0_0, v^0_1, ...., v^0_{n_0})
drone 1 : (v^1_0, v^1_1, ...., v^1_{n_1})
... 
drone m : (v^m_0, v^m_1, ...., v^m_{n_m})

Ideal start and arrival time 

drone 0 : (start(0, v^0_0, t^0_0), arrival(0, v^0_1, t^0_1), start(0, v^0_1, t^0_2), ...., arrival(0, v^0_{n_0}, t^0_{n_0}))
...

drone m : (start(m, v^m_0, t^m_0), arrival(m, v^m_1, t^m_1), start(m, v^m_1, t^m_2), ...., arrival(m, v^m_{n_m}, t^m_{n_m}))

This will create 

vertice_0 : {at(d0, t0), in (d0, t0), out(d0, t0)} .... {at(dn, tn), in (dn, tn), out(dn, tn)}  


Throughput at vertiport v at time t 

#count{d : arrival(d, v, t_{d}), moving(d, t_{d}), t-15 <= t_{d} <= t}  +
#count{d : start(d, v, t_{d}), moving(d, t_{d}), t-15 <= t_{d} <= t}

Changing starting time of a drone will affect the timeline of its destination 

m = min of starting time of some drone that violates the throughput constraint 
  = 

=======================================================================

if the sequence d0(in/out, t0), ..., dn(in/out, tn) 
t0 <= ... <= tn
violates the throughput constraint 
between [t, t+15] for t < ti, then it violates the constraint between [t0, t0+15] 

if the sequence d0(in/out, t0), ..., dn(in/out, tn) 
t0 <= ... <= tn
does not violate the throughput constraint 
between [t0, t0+15] then it does not violate the constraint between [t, t+15]
for t < t0 

=======================================================================

An algorithm for scheduling with throughput

Given graph with vertices V and a set of atoms M of the form 
  * start(d, v, s, t) 
  * arrival(d, v, s, t) 
  * next(d, s, v)
where d is a drone in the set D, v and v' are vertices in V, s is a sequence number, and t is an integer. Create a schedule for the drones that respects the throughput constraint k during time window w (#in + #out at v smaller than k for any time window w) 

Let S(v) be an array consisting of atoms of the form 
  * out(d, (v,v'), s+1, t) if start(d, v, s, t) and next(d, s, v') belong to M
  * in(d, (v',v), s, t) if arrival(d, v, s, t) and next(d, s-1, v') belong to M

S(v) should not contain repeated elements or elements of the form 
  * out(d, (v,v), _, _) 
  * in(d, (v,v), _, _) 

S(v) should be sorted by the fourth parameter (time) in the increasing order. 

max - the horizon for schedule (e.g., 180)

divide S(v) into two set Sc(v) and Sn(v) 

Initially, 
Sc(v) is empty    %consists of all elements with time 0 (completed scheduling)
Sn(v) consists of all elements with time 0 (completed scheduling)

for t = 1 to max 
    for v in V 
        if there exists no vertice such that the throughput constraint is violated 
        in [t, t+w] 
        then t = t+1 
        if there exists some vertice that violates the constraint 
            - move all atoms in and out that violates the constraints out of the range 
            - if it is the in atom, update the arrival atom of the corresponding vertices - if the atom is in Sc(v) - move back to Sn(v)
            - if it is an out atom, update the start atom of the corresponding vertices - if the atom is in Sc(v) - move back to Sn(v)

