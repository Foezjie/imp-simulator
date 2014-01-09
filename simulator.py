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
con = lite.connect('simulationDatabase.db')
with con:
    cur = con.cursor()
    #Create the tables
    cur.execute("CREATE TABLE IF NOT EXISTS Agent(Name TEXT);")
    #Unique so that we don't enter the same ID twice
    cur.execute("CREATE TABLE IF NOT EXISTS Resource(Id TEXT, UNIQUE(Id));")
    cur.execute("CREATE TABLE IF NOT EXISTS Attribute(name TEXT, value TEXT, ResourceId TEXT, UNIQUE(name,value,ResourceId));")
    cur.execute("CREATE TABLE IF NOT EXISTS Relation(name TEXT, side1ID TEXT, side2ID TEXT);")
    con.commit()


"""
Look for the different agents
"""
agent_list = set()
for res in range(0, len(parsed_json)):
    id = parsed_json[res]['id']
    parsed_id = resources.Id.parse_id(id)
    agent_list.add(parsed_id.get_agent_name())

"""
Group resources per agent
"""
agent_to_res = dict()
for agent in agent_list:
    agent_to_res[agent] = []

print("Agent to res: %s " % agent_to_res)
for res in range(0, len(parsed_json)):
    id = parsed_json[res]['id'] 
    res_agent = resources.Id.parse_id(id).get_agent_name()
    print("Agent key: %s " % res_agent)
    agent_to_res[res_agent].append(parsed_json[res])

"""
Per agent, write the resources to the database
"""

#with con:
#    cur = con.cursor()
#
#    for res in range(0, len(parsed_json)):
#        id = parsed_json[res]['id'] 
#        for attr,val in parsed_json[res].items():
#            print("Attribute %s \t Value: %s Value-type : %s" % (attr,val, type(val)))
#            if(attr == 'id'):
#                #Ignore so that we continue if the same Id is entered again
#                cur.execute("INSERT OR IGNORE INTO Resource VALUES(?)", (val,))
#            else:
#                cur.execute("INSERT OR IGNORE INTO Attribute VALUES(?, ?, ?)", (attr, str(val), id))
##select ResourceId, name, value FROM Attribute, Resource where Attribute.ResourceId = Resource.Id order by ResourceId asc;
