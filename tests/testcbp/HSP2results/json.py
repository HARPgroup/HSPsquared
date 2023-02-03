import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd
import os
os.chdir("C:/usr/local/home/git/HSPsquared")
from HSP2.utilities_specl import *
from HSP2.SPECL import specl, _specl_
from HSP2.om_model_object import *
from HSP2.om_equation import *
from HSP2.om_data_matrix import *
from HSP2.om_sim_timer import *
from HSP2.om_model_linkage import ModelLinkage, step_model_link

"""
# Use REST with authentication to load model_data
# the implementation src_json_node
src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
ssa_el_pid = 4723116 # storage_stage_area did not load, what gives?  Use this to find out
el_pid = 4723109
json_url = src_json_node + "/" + str(el_pid)
# authentication using rest un and pw
jfile = open("/var/www/python/auth.private")
jj = json.load(jfile)
rest_uname = jj[0]['rest_uname']
rest_pass = jj[0]['rest_pw']
basic = HTTPBasicAuth(rest_uname, rest_pass )
# Opening JSON file
jraw =  requests.get(json_url, auth=basic)
model_json = jraw.content.decode('utf-8')
# returns JSON object as Dict
model_data = json.loads(model_json)

# Opening local JSON file:
jfile = open("C:/usr/local/home/git/vahydro/R/modeling/nhd/nhd_simple_8566737.json")
model_data = json.load(jfile)
# returns JSON object as Dict
"""

# check class:
# model_data['object_class']
# 'hydroImpoundment'


# testing 
op_tokens, state_paths, state_ix, dict_ix, ts_ix = init_sim_dicts()
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)

# set up the timer as the first element 
timer = SimTimer('timer', False, siminfo)

#river = ModelObject('RCHRES_R001')
# upon object creation river gets added to state with path "/STATE/RCHRES_R001"
#river.add_input("Qivol", f'{river.state_path}/HYDR/IVOL', 2, True)
# a json NHD from R parser
# Opening JSON file
# load the json data from a pre-generated json file on github
json_url = "https://raw.githubusercontent.com/HARPgroup/vahydro/master/R/modeling/nhd/nhd_simple_8566737.json"
# remote file option (use auth=basic for REST request - see above "Use REST with authentication to load model_data")
jraw =  requests.get(json_url, verify=False)
model_json = jraw.content.decode('utf-8')
# returns JSON object as Dict
model_data = json.loads(model_json)
print("Loaded json with keys:", model_data.keys())

loaded_model_objects = {}
model_exec_list = {}
container = False 
# call it!
model_loader_recursive(model_data, container, loaded_model_objects)
print("Loaded the following objects/paths:", state_paths)
print("Insuring all paths are valid, and connecting models as inputs")
model_path_loader(loaded_model_objects)
print("Tokenizing models")
model_root_object = loaded_model_objects["/STATE/RCHRES_R001"]
model_tokenizer_recursive(model_root_object, loaded_model_objects, model_exec_list)
return

# debug trib_area_sqmi
# is part of equation ops bad or missing?
obj = loaded_model_objects['/STATE/RCHRES_R001/trib_area_sqmi']
ops = op_tokens[obj.ix]
# op 0 is type (1 = equation), op 1 = ix, op 2 = # of operands triplets
# experiment with adding 2, 3, 4, 5 of the 15 ops and when we reach a failure, eval = 0.0, we have found the bad op  
nops = 16
ops_test = ops[0:nops * 3 + 3]
ops_test[2] = int((len(ops_test) - 3)/3)
exec_eqn(ops_test, state_ix)



# debug Qtrib
# is part of equation ops bad or missing?
obj = loaded_model_objects['/STATE/RCHRES_R001/Qtrib']
ops = op_tokens[obj.ix]
# op 0 is type (1 = equation), op 1 = ix, op 2 = # of operands triplets
# experiment with adding 2, 3, 4, 5 of the 15 ops and when we reach a failure, eval = 0.0, we have found the bad op  
nops = 15
ops_test = ops[0:nops * 3 + 3]
ops_test[2] = int((len(ops_test) - 3)/3)
exec_eqn(ops_test, state_ix)

# now set a new value for IVOL
state_ix[state_paths['/STATE/RCHRES_R001/HYDR/IVOL']] = 60.0
test_model(op_tokens, state_ix, dict_ix, ts_ix, 1)

# explore Spring Hollow impoundment object 
# authentication using rest un and pw
jfile = open("/var/www/python/auth.private")
jj = json.load(jfile)
rest_uname = jj[0]['rest_uname']
rest_pass = jj[0]['rest_pw']
basic = HTTPBasicAuth(rest_uname, rest_pass )
src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
json_url = src_json_node + "/" + str(5428310) # spring hollow impoundment
jraw =  requests.get(json_url, auth=basic)
model_json = jraw.content.decode('utf-8')
# returns JSON object as Dict
model_data = json.loads(model_json)
mm = model_data['impoundment']['matrix']

model_loader_recursive(mm, container, loaded_model_objects)