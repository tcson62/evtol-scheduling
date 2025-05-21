import sys
import argparse
import re
import os
import subprocess
import numpy as np
# from utils.utils import EstimateMinAgents_random as get_min_agent
import toolbox


clingo_request = ["clingo"
                , "test_missing_edge.lp"                   
                , "--outf=1"       
                ]

process = subprocess.run(clingo_request, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
raw_data = process[process.index("ANSWER")+7:].split()
data = raw_data[:raw_data.index("%")]

input_data = []
for d in data:    

# Replace function name if it's a Python keyword
    d = d.replace("as(", "as_(")

    # Extract parts using regex
    match = re.match(r"(\w+)_\((\d+),\((\w+),(\w+)\),(\d+)\)", d)

    if match:
        func_name, arg1, inner1, inner2, arg3 = match.groups()
        result = f'{func_name}_({arg1}, ("{inner1}", "{inner2}"), {arg3})'
        print(result)
        input_data.append([func_name, arg1, (inner1, inner2), arg3])
    else:
        # print("No match")
        pass

# print(input_data)
for cust_id in range(1, 4):

    result = [item for item in input_data if len(item) > 1 and item[1] == str(cust_id)]
    print(result)


input_data = []
for d in data:
    match = re.match(r"(\w+)\((\d+),(\w+),(\d+)\)\.", d)
    if match:
        func_name, arg1, arg2, arg3 = match.groups()
        result = f'{func_name}({arg1}, "{arg2}", {arg3})'
        print(result)
        input_data.append([func_name, arg1, arg2, arg3])
    else:
        # print("No match found.")
        pass

# print(input_data)
cust_id = "4"
for cust_id in range(1, 7):
    result = [item for item in input_data if len(item) > 1 and item[1] == str(cust_id)]

    print(result)


        
