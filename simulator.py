#!/usr/bin/python3
import sys
import sqlite3 as lite
import json

from Imp import app
from Imp import resources

#if len(sys.argv) != 2:
#    sys.exit('Incorrect number of arguments given.\nOnly a file containing the json data can be given.\n')

with open('test.json', 'r') as data_file:    
    parsed_json = json.loads(data_file.read())

"""
Initialise the database structure
"""
def init_database():
    con = lite.connect('deployment.db')
    with con:
        cur = con.cursor()
        #Create the tables
        cur.execute("CREATE TABLE IF NOT EXISTS Agent(Name TEXT, UNIQUE(Name));")
        #Unique so that we don't enter the same ID twice
        cur.execute("CREATE TABLE IF NOT EXISTS Resource(Id TEXT, UNIQUE(Id));")
        cur.execute("CREATE TABLE IF NOT EXISTS Attribute(name TEXT, value TEXT, ResourceId TEXT, UNIQUE(name,value,ResourceId));")
        cur.execute("CREATE TABLE IF NOT EXISTS Relation(name TEXT, side1ID TEXT, side2ID TEXT);")
        con.commit()

init_database()

"""
Write a resource to the database
Returns the written resource
"""
def write_to_database(resource):
    con = lite.connect('deployment.db')
    print("Resource with id %s  written" % resource['id'])

    with con:
        cur = con.cursor()
        for attr,val in resource.items():
            if(attr == 'id'):
                #Ignore so that we continue if the same Id is entered again
                cur.execute("INSERT OR IGNORE INTO Resource VALUES(?)", (val,))
            else:
                cur.execute("INSERT OR IGNORE INTO Attribute VALUES(?, ?, ?)", (attr, str(val), id))

    return resource



"""
Look for the different agents and write them in the database
"""
agent_list = set()
for res in range(0, len(parsed_json)):
    id = parsed_json[res]['id']
    parsed_id = resources.Id.parse_id(id)
    agent_name = parsed_id.get_agent_name()
    agent_list.add(agent_name)

    #write into db
    con = lite.connect('deployment.db')
    with con:
        cur = con.cursor()
        #Ignore so that we continue if the same Id is entered again
        cur.execute("INSERT OR IGNORE INTO Agent VALUES(?)", (agent_name,))

"""
Group resources per agent
"""
agent_to_res = dict()
for agent in agent_list:
    agent_to_res[agent] = []

#print("Agent to res: %s " % agent_to_res)
for res in range(0, len(parsed_json)):
    id = parsed_json[res]['id'] 
    res_agent = resources.Id.parse_id(id).get_agent_name()
    #print("Agent key: %s " % res_agent)
    agent_to_res[res_agent].append(parsed_json[res])

def finished_deploying(agent_res_dict):
    for agent in agent_res_dict.keys():
        print("Checking if agent %s has resources left to deploy." % agent)
        if any(agent_res_dict[agent] for agent in agent_to_res.keys()):
            print("Resources left for agent %s: %s " % (agent, agent_to_res[agent]))
            return False

    return True

"""
The simulation itself
"""
#as long as not everything has been deployed
while not finished_deploying(agent_to_res):
    #deploy the resources without requirements in every agent
    for agent in agent_list:
        print("Deploying resources for agent %s." % agent)
        res_list = agent_to_res[agent]
        #by getting the list of resources without requirements, and deploying them
        no_reqs = [write_to_database(res) for res in res_list if not res['requires']]
        for agent in agent_list:
            #and getting those resources who do have requirements.
            reqs = [x for x in agent_to_res[agent] if x not in no_reqs]
            print("Resources without requirements: %s \n Resources with requirements: %s" % (len(no_reqs), len(reqs)))
            #Then remove the written resources from the requirements of the remaining resources
            for res in reqs:
                for possible_req in no_reqs:
                    print("Checking if %s can be removed from the requirements of %s." % (possible_req['id'], res['id']))
                    if possible_req['id'] in res['requires']:
                        print("Removed %s from the requirements of %s." % (possible_req, res))
                        res['requires'].remove(possible_req['id'])

            #In the end we remove the newly deployed resources from the resource list of the agent.
            agent_to_res[agent] = reqs




##select ResourceId, name, value FROM Attribute, Resource where Attribute.ResourceId = Resource.Id order by ResourceId asc;
