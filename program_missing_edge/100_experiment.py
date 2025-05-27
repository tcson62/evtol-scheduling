import sys
import argparse
import os
import subprocess
import numpy as np
# from utils.utils import EstimateMinAgents_random as get_min_agent
import toolbox

results = ""
for i in range(0, 100):
    seed = i
    print("seed:", seed)    
    # request_text, cust_set = generate_random_request(seed, "instances/rq_random.lp")
    # request_text += "\n"
    # # print(request_text)
    # # print("_______________________________________________________________________")

    # # print(np.array(cust_set))
    cust_set = toolbox.GenRq(30, 1, seed)
    cust_num = np.sum(cust_set)
    required_agent_num = toolbox.EstimateMinAgents_random(180, cust_set, 4)
    segment = toolbox.EstimateMinSegment(required_agent_num, cust_set, 4)
    print("segment", segment)
    # Generate drone
    toolbox.InitLoc(required_agent_num, seed, 12)
    try:
        # run schedule assign customer flight
        # clingo encoding/s.lp instances/network_NY_0.lp -c start_seg=1 -c max_seg=13 -c horizon=180 --heuristic=Domain -t4 --outf=1
        clingo_request = ["clingo"
                        , "encoding/s.lp"
                        , "instances/network_NY_0.lp"
                        , "instances/init.lp"
                        , "instances/rq.lp"
                        , "-c", "start_seg=1"
                        # , "-c", "max_seg={segment}".format(segment=segment)
                        , "-c", "max_seg=13"
                        , "-c", "horizon=180"
                        , "--heuristic=Domain"   
                        , "-t4"
                        , "--outf=1"
                        ]

        process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        print(process)

        # preprocess schedule assign customer flight
        output_1 = process[process.index("ANSWER")+7:process.index("\nCOST")]
        # print(output_1)
        with open("results/output_1.lp", "w") as f:
            f.write(output_1)

        f.close()
        print("finish schedule assign customer flight")
        # run switching
        clingo_request = ["clingo"
                        , "encoding/swap0.1.lp"
                        , "instances/network_NY_0.lp"
                        , "results/output_1.lp"                   
                        , "-c", "horizon=180"
                        , "--time-limit=8"                   
                        , "--outf=1"
                        ]

        process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        print("process:", process)




