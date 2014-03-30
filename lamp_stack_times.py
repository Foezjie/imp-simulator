#!/usr/bin/env python3

import subprocess
import re
import timeit
import random
import json
import pprint
from Imp import app
from Imp import resources

pp = pprint.PrettyPrinter(indent=2)

deploy_re = re.compile(".*Resource with id\s(.*)\swritten")
srv_regex = re.compile(".*std::Service.*")
pkg_regex = re.compile(".*std::Package.*")
cfg_regex = re.compile(".*std::File.*")
srv_regex = re.compile(".*std::Service.*")

exceptions = ["network", "firewalld"] #Some services are standard in the Fedora installation and don't have a package in the model
ignored_files = ['/etc/flens.d/collectd_in.json', '/etc/ssh/sshd_config']

deployments = []

def avg(numbers):
    return float((sum(numbers)/len(numbers)))

def read_order(json):
    depl_order = {}
    file_to_name = {}
    for res in json:
        res_agent = resources.Id.parse_id(res['id']).get_agent_name()
        res_value = resources.Id.parse_id(res['id']).get_attribute_value()
        if not res_value in ignored_files:
            if srv_regex.match(res['id']):
                if res['name'] not in exceptions:
                    pkg_file_reg = re.compile("std::(Package|File).*%s.*%s.*" % (res_agent, res['name'])) #Only add same agent resources
                    depl_order[(res['name'], res_agent)] = [req['id'] for req in json if pkg_file_reg.match(req['id']) and not any([req['id'] in list for list in depl_order.values()]) and not resources.Id.parse_id(req['id']).get_attribute_value() in ignored_files] #Don't add a file twice on different services
            elif pkg_regex.match(res['id']):
                if res['name'] == "cassandra12":
                    res['name'] = "cassandra"
                file_reg = re.compile("std::File.*%s.*%s.*" % (res_agent, res['name'])) #Only add same agent resources
                for file in json:
                    if file_reg.match(file['id']):
                        file_to_name[file['id']] = (res['name'], res_agent)

    return (depl_order, file_to_name)

def packages_left(requires):
    return any([pkg_regex.match(req) for req in requires])

def files_left(requires):
    return any([cfg_regex.match(req) for req in requires])

def corresponding_name_agent(file_id, file_to_name):
    if file_id in file_to_name:
        return file_to_name[file_id]
    else:
        return (None, None)

def do_measure():
    global deployments
    deploy_order = {}

    subprocess.call("rm -f deployment.db", shell=True)
    print("-------------------\n   Starting new run \n-------------------")

    """
    Shuffle the json to simulate different deployments
    """
    with open('test.json', 'r') as data_file:
        parsed_json = json.loads(data_file.read())

    random.shuffle(parsed_json)
    (deploy_order, file_to_name) = read_order(parsed_json)

    with open('test.json', 'w') as data_file:
        json.dump(parsed_json, data_file)

    times = 0
    deployed = 0
    while deploy_order:
        times = times + 1
        print("starting simulator...")
        subprocess.call("./simulator.py 2> /tmp/timing_log", shell=True)
        print("simulating done.")

        with open('/tmp/timing_log','r') as f:
                log = f.readlines()
        
        for line in log:
            line_match = deploy_re.match(line)
            if line_match is not None:
                line_id = line_match.groups()[0]
                #print("Line: %s" % line)
                res_name = resources.Id.parse_id(line_id).get_attribute_value() #name bij srv/pkg, path bij file
                res_type = resources.Id.parse_id(line_id).get_entity_type()
                res_agent = resources.Id.parse_id(line_id).get_agent_name()

                if res_type == "std::Package":
                    if res_name == "cassandra12":
                        res_name = "cassandra"
                    if (res_name, res_agent) in deploy_order and packages_left(deploy_order[(res_name, res_agent)]):
                        if line_id in deploy_order[(res_name, res_agent)]:
                            deploy_order[(res_name, res_agent)].remove(line_id) #remove the package from the list
                            #print("%s verwijderd uit deploy_order." % line_id)
                            deployed = deployed + 1

                elif res_type == "std::File":
                    (pkg_name, agent) = corresponding_name_agent(line_id, file_to_name)
                    if pkg_name is not None and (pkg_name, res_agent) in deploy_order:
                        if not packages_left(deploy_order[(pkg_name, res_agent)]):
                            if line_id in deploy_order[(pkg_name, res_agent)]:
                                deploy_order[(pkg_name, res_agent)].remove(line_id) #remove the file from the list
                                #print("%s verwijderd uit deploy_order." % line_id)
                                deployed = deployed + 1

                elif res_type == "std::Service":
                    if (res_name, res_agent) in deploy_order and not packages_left(deploy_order[(res_name, res_agent)]) and not files_left(deploy_order[(res_name, res_agent)]):
                        deploy_order.pop((res_name, res_agent), None)
                        #print("Service %s volledig uitgerold." % line_id)
                        deployed = deployed + 1
        print("Deployed this run: %s" % deployed)
        pp.pprint(deploy_order)
        deployed = 0

    deployments.append(times)

avg_time = timeit.timeit("do_measure()", setup="from __main__ import do_measure", number=3)/3
print("Avg time: %s" % avg_time)
print("Deployments avg: %s\nDeployments %s" % (avg(deployments), deployments))
