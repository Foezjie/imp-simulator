#!/usr/bin/env python3

import subprocess
import re
import timeit
import random
import json
import pprint

import copy

from Imp import app
from Imp import resources

pp = pprint.PrettyPrinter(indent=2)

deploy_re = re.compile(".*Resource with id\s(.*)\swritten")
srv_regex = re.compile(".*std::Service.*")
pkg_regex = re.compile(".*std::Package.*")
cfg_regex = re.compile(".*std::File.*")
srv_regex = re.compile(".*std::Service.*")

exceptions = ["network", "firewalld"] #Some services are standard in the Fedora installation and don't have a package in the model
ignored_files = ['/etc/ssh/sshd_config']

deployments = []

def avg(numbers):
    return float((sum(numbers)/len(numbers)))

def read_order(json):
    requires = {}

    for res in json:
        requires[res['id']] = res['requires']

    return requires

def packages_left(requires):
    return any([pkg_regex.match(req) for req in requires])

def files_left(requires):
    return any([cfg_regex.match(req) for req in requires])

def corresponding_name_agent(file_id, file_to_name):
    if file_id in file_to_name:
        return file_to_name[file_id]
    else:
        return (None, None)

def find_and_delete_provider(requires, provider_id):
    depl = 0
    requires_new = copy.deepcopy(requires)
    for res, reqs in requires.items():
        if provider_id in reqs:
            res_name = resources.Id.parse_id(res).get_attribute_value()
            provider = resources.Id.parse_id(provider_id).get_attribute_value()
            requires_new[res].remove(provider_id)
            depl = depl + 1
            print("Removed %s from requires of %s." % (provider, res_name))


    return (requires_new, depl)

def do_measure():
    global deployments

    print("Removing old timing logs")
    subprocess.call("rm -f /tmp/timing_log*", shell=True)
    print("Removing old deployment db")
    subprocess.call("rm -f deployment.db", shell=True)
    print("-------------------\n   Starting new run \n-------------------")

    """
    Shuffle the json to simulate different deployments
    """
    with open('test.json', 'r') as data_file:
        parsed_json = json.loads(data_file.read())

    random.shuffle(parsed_json)
    requires = read_order(parsed_json)

    with open('test.json', 'w') as data_file:
        json.dump(parsed_json, data_file)

    times = 0
    while requires:
        deployed = 0
        times = times + 1
        print("starting simulator...")
        subprocess.call("./simulator.py 2> /tmp/timing_log%s" % times, shell=True)
        print("simulating done.")

        with open('/tmp/timing_log%s' % times,'r') as f:
                log = f.readlines()
        
        for line in log:
            line_match = deploy_re.match(line)
            if line_match is not None:
                line_id = line_match.groups()[0]

                if line_id in requires and not requires[line_id]:
                    (requires, amnt) = find_and_delete_provider(requires, line_id)
                    deployed = deployed + amnt

                    if not requires[line_id]: #Remove empty requires
                        requires.pop(line_id)
                        deployed = deployed + 1
                        print("%s fully deployed." % line_id)

        print("Deployed this run: %s" % deployed)
        pp.pprint(requires)

    deployments.append(times)

avg_time = timeit.timeit("do_measure()", setup="from __main__ import do_measure", number=1)/1
print("Avg time: %s" % avg_time)
print("Deployments avg: %s\nDeployments %s" % (avg(deployments), deployments))

