vertiport(jfk;lga;teb;ryend;cri;cimbl;dandy).
distance((jfk, jfk), 0).
distance((jfk, teb), 19).
distance((jfk, dandy), 20).
distance((lga, jfk), 10).
distance((lga, lga), 0).
distance((lga, cri), 11).
distance((lga, dandy), 13).
distance((teb, jfk), 19).
distance((teb, teb), 0).
distance((teb, cri), 16).
distance((teb, cimbl), 6).
distance((teb, dandy), 6).
distance((ryend, lga), 15).
distance((ryend, teb), 11).
distance((ryend, ryend), 0).
distance((ryend, cimbl), 9).
distance((cri, jfk), 6).
distance((cri, lga), 11).
distance((cri, ryend), 13).
distance((cri, cri), 0).
distance((cri, dandy), 16).
distance((cimbl, lga), 7).
distance((cimbl, ryend), 9).
distance((cimbl, cimbl), 0).
distance((cimbl, dandy), 7).
distance((dandy, jfk), 20).
distance((dandy, ryend), 6).
distance((dandy, dandy), 0).
flight_time((jfk, jfk), 0).
flight_time((jfk, teb), 11).
flight_time((jfk, dandy), 12).
flight_time((lga, jfk), 6).
flight_time((lga, lga), 0).
flight_time((lga, cri), 6).
flight_time((lga, dandy), 8).
flight_time((teb, jfk), 11).
flight_time((teb, teb), 0).
flight_time((teb, cri), 10).
flight_time((teb, cimbl), 4).
flight_time((teb, dandy), 4).
flight_time((ryend, lga), 9).
flight_time((ryend, teb), 7).
flight_time((ryend, ryend), 0).
flight_time((ryend, cimbl), 5).
flight_time((cri, jfk), 3).
flight_time((cri, lga), 6).
flight_time((cri, ryend), 8).
flight_time((cri, cri), 0).
flight_time((cri, dandy), 10).
flight_time((cimbl, lga), 4).
flight_time((cimbl, ryend), 5).
flight_time((cimbl, cimbl), 0).
flight_time((cimbl, dandy), 4).
flight_time((dandy, jfk), 12).
flight_time((dandy, ryend), 4).
flight_time((dandy, dandy), 0).
charge_time((jfk, jfk), 0).
charge_time((jfk, teb), 18).
charge_time((jfk, dandy), 19).
charge_time((lga, jfk), 10).
charge_time((lga, lga), 0).
charge_time((lga, cri), 10).
charge_time((lga, dandy), 13).
charge_time((teb, jfk), 18).
charge_time((teb, teb), 0).
charge_time((teb, cri), 15).
charge_time((teb, cimbl), 6).
charge_time((teb, dandy), 6).
charge_time((ryend, lga), 14).
charge_time((ryend, teb), 11).
charge_time((ryend, ryend), 0).
charge_time((ryend, cimbl), 8).
charge_time((cri, jfk), 6).
charge_time((cri, lga), 10).
charge_time((cri, ryend), 13).
charge_time((cri, cri), 0).
charge_time((cri, dandy), 15).
charge_time((cimbl, lga), 6).
charge_time((cimbl, ryend), 8).
charge_time((cimbl, cimbl), 0).
charge_time((cimbl, dandy), 7).
charge_time((dandy, jfk), 19).
charge_time((dandy, ryend), 6).
charge_time((dandy, dandy), 0).
edge((jfk, jfk)).
edge((jfk, teb)).
edge((jfk, dandy)).
edge((lga, jfk)).
edge((lga, lga)).
edge((lga, cri)).
edge((lga, dandy)).
edge((teb, jfk)).
edge((teb, teb)).
edge((teb, cri)).
edge((teb, cimbl)).
edge((teb, dandy)).
edge((ryend, lga)).
edge((ryend, teb)).
edge((ryend, ryend)).
edge((ryend, cimbl)).
edge((cri, jfk)).
edge((cri, lga)).
edge((cri, ryend)).
edge((cri, cri)).
edge((cri, dandy)).
edge((cimbl, lga)).
edge((cimbl, ryend)).
edge((cimbl, cimbl)).
edge((cimbl, dandy)).
edge((dandy, jfk)).
edge((dandy, ryend)).
edge((dandy, dandy)).

edge_loop((V,V)) :- edge((V,V)).