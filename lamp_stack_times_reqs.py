#!/usr/bin/env python3

import subprocess
import re
import timeit
import random
import json
import pprint
pp = pprint.PrettyPrinter(indent=2)
import copy
from Imp import app
from Imp import resources



deploy_re = re.compile(".*Resource with id\s(.*)\swritten")

deployments = []

def avg(numbers):
    return float((sum(numbers)/len(numbers)))

def id_val(_id):
    return resources.Id.parse_id(_id).get_attribute_value()

def id_agent(_id):
    return resources.Id.parse_id(_id).get_agent_name()

def id_type(_id):
    return resources.Id.parse_id(_id).get_entity_type()

#Read the requirements from the json that has "all" the correct requirements.
#"All" in the sense of: it can deploy the model in one run.
#Can't work with the normal id's because they contain a version number
def read_order():
    with open('test.json', 'r') as data:
        req_json = json.loads(data.read())

    requires = {}
    for res in req_json:
        requires[(id_type(res['id']), id_agent(res['id']), id_val(res['id']))] = [(id_type(req), id_agent(req), id_val(req)) for req in res['requires']]

    return requires

def find_and_delete_provider(requires, index):
    depl = 0
    requires_new = copy.deepcopy(requires)
    for res, reqs in requires.items():
        if index in reqs:
            requires_new[res].remove(index)
            #print("%s removed from the requirements of %s" % (index, res))
            depl = depl + 1

    return (requires_new, depl)

def do_measure():
    global deployments
    depl_list = []

    #print("Removing old timing logs")
    subprocess.call("rm -f /tmp/timing_log*", shell=True)
    #print("Removing old deployment db")
    subprocess.call("rm -f deployment.db", shell=True)
    #print("-------------------\n   Starting new run \n-------------------")

    """
    Shuffle the json to simulate different deployments
    """
    with open('test.json', 'r') as data_file:
        parsed_json = json.loads(data_file.read())

    random.shuffle(parsed_json)
    requires = read_order()

    with open('test.json', 'w') as data_file:
        json.dump(parsed_json, data_file)

    times = 0
    while requires:
        deployed = 0
        times = times + 1
        #print("starting simulator...")
        subprocess.call("./simulator.py 2> /tmp/timing_log%s" % times, shell=True)
        #print("simulating done.")

        with open('/tmp/timing_log%s' % times, 'r') as f:
                log = f.readlines()
        
        for line in log:
            line_match = deploy_re.match(line)
            if line_match is not None:
                line_id = line_match.groups()[0]

                index = (id_type(line_id), id_agent(line_id), id_val(line_id))
                if index in requires and not requires[index]: #First "deploy" resources with no requirements
                    requires.pop(index)
                    deployed = deployed + 1
                    #print("%s fully deployed." % line_id)
                    
                    #update the requires map: delete the newly deployed resource
                    (requires, amnt) = find_and_delete_provider(requires, index)
                    deployed = deployed + amnt

        depl_list.append(deployed)
        #print("Deployed this run: %s" % deployed)
        #pp.pprint(requires)
    deployments.append(depl_list)


avg_time = timeit.timeit("do_measure()", setup="from __main__ import do_measure", number=1)/1
print("Avg time: %s" % avg_time)
print("No. of deployments:%s Deployments avg: %s\nDeployments %s" % (len(deployments), avg([avg(l) for l in deployments]), deployments))
