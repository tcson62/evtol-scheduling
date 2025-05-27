import sys
import random
import os
import numpy as np
import math
import re

# utils.py function =============================================================

velocity = 100 # mph
e_dischg = 4 # kWh/mile
e_max = 100 # kWh
g_i=250 # kW

dist = np.array(
    [
        [0.,          10.48113508,  18.51467981,  18.54127528,  5.7385456,    13.03650962,  20.09902115], 
        [10.48113508,  0.,           9.15619145,   15.04929904,  10.56004164,  6.52505341,   13.22524436],
        [18.51467981,  9.15619145,   0.,           11.47944457,  16.1038714,   6.31668958,   6.33708216 ],
        [18.54127528,  15.04929904,  11.47944457,  0.,           13.32823709,  8.5872692,    6.16996146 ],
        [5.7385456,    10.56004164,  16.1038714,   13.32823709,  0.,           9.86908414,   16.01052999],
        [13.03650962,  6.52505341,   6.31668958,   8.5872692,    9.86908414,   0.,           7.31033037 ],
        [20.09902115,  13.22524436,  6.33708216,   6.16996146,   16.01052999,  7.31033037,   0.         ]
        ]
    )

def EstimateMinAgents_random(horizon, demand_cust_set, aircraft_capacity):        
    
    minimum_flights_per_edge = np.ceil(demand_cust_set/aircraft_capacity)
    require_operation_time_each_edge_set = dist*(60/velocity + e_dischg*60/g_i) * minimum_flights_per_edge
    require_operation_time_serve_all_cust = np.sum(require_operation_time_each_edge_set)
    min_number_agents = math.ceil(require_operation_time_serve_all_cust/horizon)
    
    return min_number_agents

def EstimateMinSegment(min_number_agents, demand_cust_set, aircraft_capacity):
    minimum_flights_per_edge = np.ceil(demand_cust_set/aircraft_capacity)
    segment = math.ceil(np.sum(minimum_flights_per_edge)/min_number_agents)
    return segment

# gen_instance.py function =============================================================
vPort_id = ["jfk", "lga", "teb", "ryend", "cri", "cimbl", "dandy"]

def InitLoc(nAgents, seed, limit_nAgents_each_vertiport):
    # input arguments, need nAgents and seed

    random.seed(seed)
    fName = 'instances/init.lp'
    backup_fname = "instances/init/init_{seed}.lp".format(seed=seed)
    decoupled_init_fName = 'instances/init_decoupled.lp'
    #init location
    #discharge rate
    #emax
    #emin

    emax_print = [[i, 60] for i in range(0, nAgents)]
    emin_print = [[i, 0] for i in range(0, nAgents)]
    dischg_rate_print = [[i, 4] for i in range(0, nAgents)]
    capacity_print = [[i, 4] for i in range(0, nAgents)]
    init_loc_print = []
    # init_loc = np.arange(nAgents)%(len(vPort_id))
    init_loc = []
    counts = {}
    for i in range(nAgents):
        while True:
            val = random.randint(0, len(vPort_id)-1)
            if counts.get(val, 0) < limit_nAgents_each_vertiport:
                counts[val] = counts.get(val, 0) + 1
                init_loc.append(val)
                break
    for i in range(0, nAgents):
        init_loc_print += [[i, vPort_id[init_loc[i]]]]


    counts = {}  # Dictionary to count occurrences of each random number


    init_battery_print = []
    for i in range(0, nAgents):
        init_battery_print += [[i, 60]]
        
        
    variable = [init_loc_print, emax_print, emin_print, dischg_rate_print, capacity_print, init_battery_print]
    atoms_name = ['init_loc', 'emax', 'emin', 'dischg_rate', 'capacity', 'b_init']

    # # new_file_name = "instances/recorded_init/init_{seed}.lp".format(seed = seed)
    # f = open(decoupled_init_fName,"w+")
    # #AGENT
    # # f.write('agent('+str(0)+'..'+str(nAgents-1)+').\n')
    # f.write(f"%battery in minute.\n")
    # for var, atom_name in zip(variable, atoms_name):
    #     for i in var:
    #         f.write(atom_name + str(tuple(i)).replace("'","") + '.\n')
    # f.close()

    backup_f = open(fName,"w+")
    #AGENT
    backup_f.write('agent('+str(0)+'..'+str(nAgents-1)+').\n')
    for var, atom_name in zip(variable, atoms_name):
        for i in var:
            backup_f.write(atom_name + str(tuple(i)).replace("'","") + '.\n')
    backup_f.close()

    backup_f = open(backup_fname,"w+")
    #AGENT
    backup_f.write('agent('+str(0)+'..'+str(nAgents-1)+').\n')
    for var, atom_name in zip(variable, atoms_name):
        for i in var:
            backup_f.write(atom_name + str(tuple(i)).replace("'","") + '.\n')
    backup_f.close()    

def GenRq(cust, random_flag = 1, seed = 0, file_loc = 'instances/rq.lp', backup_loc = 'instances/rq/'):
    
    # random_flag = 1    
    
    if random_flag != 0:
        random.seed(seed)
    request_p = [[j, i] for i in range(0, 7) for j in range(0, 7) if i != j]
    
    matrix_out = [[random.randint(0, cust) if i!=j else 0 for j in range(0, len(vPort_id))] for i in range(0, len(vPort_id))]
    
    request_p = [[vPort_id[m[0]], vPort_id[m[1]]]for m in request_p]
    request_print = []
    total_edge = len(vPort_id) * (len(vPort_id)-1)
    
    for i in range(0, total_edge):
        no = i
        origin = request_p[i][0] 
        destination = request_p[i][1]
        
        if random_flag == 0:
            request_print += [[no, (origin, destination), cust]]
        else:            
            cust_rand = matrix_out[vPort_id.index(origin)][vPort_id.index(destination)]
            
            request_print += [[no, (origin, destination), cust_rand]]

    f = open(file_loc,"w+")
    # f = open("rq.lp", "w+")
    f.write(f'%{matrix_out}')
    f.write('%request(ID, (edge), number of request passenger)\n')
    for i in request_print:
        f.write('request' + str(tuple(i)).replace("'","") + '.\n')

    f.close()

    f_backup = open(backup_loc + 'rq_{seed}.lp'.format(seed = seed),"w+")
    f_backup.write(f'%{matrix_out}')
    f_backup.write('%request(ID, (edge), number of request passenger)\n')
    for i in request_print:
        f_backup.write('request' + str(tuple(i)).replace("'","") + '.\n')
    f_backup.close()    
    print(request_print)
    return np.array(matrix_out)

#GenRq for missing edge ======================================================================================
def GenRq_missing_edge(cust, random_flag = 1, seed = 0, file_loc = 'instances/rq.lp', backup_loc = 'instances/rq/'):
    ID_count = 1
    if random_flag != 0:
        random.seed(seed)
    request_p = [[j, i] for i in range(0, 7) for j in range(0, 7) if i != j]
    
    matrix_out = [[random.randint(0, cust) if i!=j else 0 for j in range(0, len(vPort_id))] for i in range(0, len(vPort_id))]
    
    request_p = [[vPort_id[m[0]], vPort_id[m[1]]]for m in request_p]
    request_print = []
    total_edge = len(vPort_id) * (len(vPort_id)-1)
    
    for i in range(0, total_edge):
        no = i
        origin = request_p[i][0] 
        destination = request_p[i][1]
        
        if random_flag == 0:
            request_print += [[no, (origin, destination), cust]]
        else:            
            cust_rand = matrix_out[vPort_id.index(origin)][vPort_id.index(destination)]
            
            request_print += [[no, (origin, destination), cust_rand]]

    f = open(file_loc,"w+")
    # f = open("rq.lp", "w+")
    result = ""
    f.write(f"%{matrix_out} \n")
    result += f"%{matrix_out} \n"
    f.write('%customer(ID, loc, des)\n')
    result += '%customer(ID, loc, des)\n'
    for i in request_print:
        for cust in range(i[2]):
            f.write("customer({ID}, {loc}, {des}).\n".format(ID = ID_count, loc = i[1][0], des = i[1][1]))
            result += "customer({ID}, {loc}, {des}).\n".format(ID = ID_count, loc = i[1][0], des = i[1][1])
            ID_count += 1
    # return np.array(matrix_out)
    return result

def InitLoc_missing_edge(nAgents, seed, limit_nAgents_each_vertiport):
    # input arguments, need nAgents and seed

    random.seed(seed)
    fName = 'instances/init.lp'
    backup_fname = "instances/init/init_{seed}.lp".format(seed=seed)
    decoupled_init_fName = 'instances/init_decoupled.lp'
    #init location
    #discharge rate
    #emax
    #emin

    emax_print = [[i, 60] for i in range(1, nAgents+1)]
    emin_print = [[i, 0] for i in range(1, nAgents+1)]
    dischg_rate_print = [[i, 4] for i in range(1, nAgents+1)]
    capacity_print = [[i, 4] for i in range(1, nAgents+1)]
    init_loc_print = []
    # init_loc = np.arange(nAgents)%(len(vPort_id))
    init_loc = []
    counts = {}
    for i in range(nAgents):
        while True:
            val = random.randint(0, len(vPort_id)-1)
            if counts.get(val, 0) < limit_nAgents_each_vertiport:
                counts[val] = counts.get(val, 0) + 1
                init_loc.append(val)
                break
    for i in range(0, nAgents):
        init_loc_print += [[i+1, vPort_id[init_loc[i]]]]


    counts = {}  # Dictionary to count occurrences of each random number


    init_battery_print = []
    for i in range(1, nAgents+1):
        init_battery_print += [[i, 60]]
        
        
    variable = [init_loc_print, emax_print, emin_print, dischg_rate_print, capacity_print, init_battery_print]
    atoms_name = ['init_loc', 'emax', 'emin', 'dischg_rate', 'capacity', 'b_init']
    result = ""

    backup_f = open(fName,"w+")
    #AGENT
    backup_f.write('agent('+str(1)+'..'+str(nAgents)+').\n')
    result += 'agent('+str(1)+'..'+str(nAgents)+').\n'

    for var, atom_name in zip(variable, atoms_name):
        for i in var:
            backup_f.write(atom_name + str(tuple(i)).replace("'","") + '.\n')
            result += atom_name + str(tuple(i)).replace("'","") + '.\n'
    backup_f.close()

    backup_f = open(backup_fname,"w+")
    #AGENT
    backup_f.write('agent('+str(1)+'..'+str(nAgents)+').\n')
    for var, atom_name in zip(variable, atoms_name):
        for i in var:
            backup_f.write(atom_name + str(tuple(i)).replace("'","") + '.\n')
    backup_f.close()    
    return result


# gen_map.py function =============================================================

# chances goes from 0-100, where 0 never and 100 is all the time
def lotto_paths(edges, rate, seed):
    random.seed(seed)
    output = []
    for edge in edges:
        if edge[0] == edge[1]:
            output.append(edge)
            continue
        roll = random.randint(0, 99)
        if roll < rate:
            output.append(edge)
    return output


def extract_info(keyword, data, regex = r"{keyword}\(\((\w+), (\w+)\), (\d+)\)"):
    output = []
    for d in data:
        # print(d)
        key_sentence = regex.format(keyword=keyword)
        # print(key_sentence)
        match = re.match(key_sentence, d)
        # match = re.match(r"distance\(\((\w+), (\w+)\), (\d+)\)", d)
        if match:
            # print(d)            
            output.append(list(match.groups()))
    return output

def preprocess_map(seed, rate):
    distance_set = ""
    with open("instances/network_NY_0.lp", "r") as f:
        distance_set = f.read()

    raw_data = distance_set.split("\n")
    vertiports_data = raw_data[0]
    vertiports = vertiports_data[vertiports_data.index("(")+1:vertiports_data.index(")")].split(";")
    # print(vertiports)

    distance = extract_info("distance", raw_data)    
    flight_time = extract_info("flight_time", raw_data)    
    charge_time = extract_info("charge_time", raw_data)    
    edge = extract_info("edge", raw_data, regex=r"{keyword}\(\((\w+),(\w+)\)\)")
    
    full_data = "vertiport(jfk;lga;teb;ryend;cri;cimbl;dandy).\n"
    qualify_paths = lotto_paths(edge, rate, seed)
    # print(qualify_paths)
    # print()
    for i in distance:        
        if i[0:2] in qualify_paths:
            full_data += "distance(({start}, {des}), {num}).\n".format(start = i[0], des = i[1], num = i[2])
    
    for i in flight_time:        
        if i[0:2] in qualify_paths:
            full_data += "flight_time(({start}, {des}), {num}).\n".format(start = i[0], des = i[1], num = i[2])
    
    for i in charge_time:        
        if i[0:2] in qualify_paths:
            full_data += "charge_time(({start}, {des}), {num}).\n".format(start = i[0], des = i[1], num = i[2])
    
    for i in edge:        
        if i[0:2] in qualify_paths:
            full_data += "edge(({start}, {des})).\n".format(start = i[0], des = i[1])
    
    full_data += "\nedge_loop((V,V)) :- edge((V,V))."
    # with open("instances/network_NY_0_rand.lp", "w") as f:
    #     f.write(full_data)
    # f.close()
    return full_data

if __name__ == "__main__":
    preprocess_map(10, 50)
