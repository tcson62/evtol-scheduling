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

        #preprocess switching:

        output_2 = process[process.index("ANSWER")+7:process.index(").\n")+2]
        # print(output_2)

        with open("results/output_2.lp", "w") as f:
            f.write(output_2)

        f.close()

        print("finish switching")

        # assign time, don't have horizon
        clingo_request = ["clingo-dl"
                        , "encoding/time0.lp"                   
                        , "results/output_2.lp"
                        , "--outf=1"
                        ]

        process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        # print("process:", process)

        # preprocess time
        output_3 = process[process.index("ANSWER")+7:process.index(").\n")+2]

        with open("results/output_3.lp", "w") as f:
            f.write(output_3)

        f.close()

        # check over 180
        clingo_request = ["clingo"
                        , "results/check_dl.lp"                   
                        , "results/output_3.lp"
                        , "--outf=1"
                        ]

        process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        if "UNSATISFIABLE" in process:
            result = "N"
        else:
            result = "Y"

        print("finish {seed}".format(seed = seed))
        # write out for visualize
        output = output_2 + " " + output_3

        with open("results/trajectories/trajectories_{seed}.lp".format(seed=seed), "w") as f:
            f.write(output)
        f.close()
    except:
        result = "ERR"

    with open("results/100_runs.txt", "a+") as f:
        f.write("{seed} {result}\n".format(seed=seed, result = result))
    f.close()
    data = "{cust_num}_{drone_num}_{segment_num}_{result}\n".format(cust_num=cust_num, drone_num=required_agent_num, segment_num=segment, result=result)
    with open("results/instances.txt", "a+") as f:
        f.write(data)
    f.close()



# clingo_request = ["python"
#                    , "instances/gen_init_random_NY.py"
#                    , str(required_agent_num)
#                    , str(seed)
#                    , "100"                
#                    ]

# process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# request_text += process.stdout[:-1] # the output
# print(request_text)
# # with open("instances/rq_random.lp", "w") as f:
# #     f.write(request_text) 


# with open("instances/profile_{seed}.lp".format(seed = seed), "w") as f:
#     f.write(request_text)


