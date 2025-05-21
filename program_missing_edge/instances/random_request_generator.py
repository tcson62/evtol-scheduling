# rq random generator, put seed as first parameter when run for consistent result

import random
import sys
import numpy as np

# random int number generator:
def random_cust_num(min = 0, max = 30):
    return random.randint(min, max)

def generate_random_request(seed, file_name):
    vPort_id = ["jfk", "lga", "teb", "ryend", "cri", "cimbl", "dandy"]

    # # will use seed if has seed:
    # try:
    #     seed = int(sys.argv[1])
    #     random.seed(seed)
    # except:
    #     pass

    random.seed(seed)
    text = ""
    count = 0
    cust_list = []
    for des in vPort_id:
        single_node = []
        for start in vPort_id:
            cust_num = random_cust_num()
            
            if start != des:                
                single_node.append(cust_num)
                request_text = "request({id}, ({start}, {des}), {customer_num})".format(des = des, start = start, id = count, customer_num=cust_num)
                text += request_text + ".\n"            
                count += 1
            else:
                single_node.append(0)
        cust_list.append(single_node)

    # print("finish generating")

    # print(text[:-1])
    # Change output filename here:
    with open(file_name, "w") as f:
        f.write(text[:-1]) # remove \n at the end
    
    return text[:-1], np.array(cust_list)

