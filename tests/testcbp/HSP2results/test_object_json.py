# put changeable stuff here
src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
#el_pid = 7113514 # Greenville County New Reservoir: 5356344, Chesdin WTP: 4828385, new Chesdin 6.4 7113514, Crozet BC 
#river_pid = 4431664 # also, load the river
if not ("el_pid" in locals()):
    print("*************************************")
    print("ERROR: You must define el_pid before running this code")
    print("*************************************")

import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd
from pandas import HDFStore, Timestamp, read_hdf, DataFrame, date_range
from pandas.tseries.offsets import Minute
import os
os.chdir("C:/usr/local/home/git/HSPsquared")
from numpy import zeros, any, full, nan, array, int64, arange
from math import sqrt, log10
from numba import njit
from numba.typed import List
from HSP2.utilities import initm, make_numba_dict
from HSP2.state import *
from HSP2.om import *
from HSP2.om_model_object import *
from HSP2.om_sim_timer import *
from HSP2.om_equation import *
from HSP2.om_model_linkage import *
from HSP2.om_data_matrix import *
from HSP2.om_model_broadcast import *
from HSP2.utilities import versions, get_timeseries, expand_timeseries_names, save_timeseries, get_gener_timeseries
from HSP2.SPECL import specl


domain = "/STATE/RCHRES_R001/HYDR" # any objects that are connected to this object should be loaded 
# initialize runtime Dicts
op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache = init_sim_dicts()
model_object_cache = {}
# set on object root class for global sharing
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (op_tokens, state_paths, state_ix, dict_ix, model_object_cache)
# set up info and timer
siminfo = {}
siminfo['delt'] =60
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)
# Set up basic hsp2 things for state
hydr_init_ix(state_ix, state_paths, domain)
# base array for the model json inputs before parsing
model_data = {}

# authentication using rest un and pw
jfile = open("/var/www/python/auth.private")
jj = json.load(jfile)
rest_uname = jj[0]['rest_uname']
rest_pass = jj[0]['rest_pw']
basic = HTTPBasicAuth(rest_uname, rest_pass )

# Should we load a river segment or just create a shell?
if not ("river_pid" in locals()):
    model_data['RCHRES_R001'] = {}
    model_data['RCHRES_R001']['name'] = 'RCHRES_R001'
    model_data['RCHRES_R001']['object_class'] = 'ModelObject'
else: 
    # load the model container from json too 
    json_url = src_json_node + "/" + str(river_pid)
    jraw =  requests.get(json_url, auth=basic)
    river_json = jraw.content.decode('utf-8')
    # returns JSON object as Dicts
    river_model = json.loads(river_json)
    model_name = list(river_model.keys())[0]
    model_data['RCHRES_R001'] = river_model[model_name]
    model_data['RCHRES_R001']['name'] = 'RCHRES_R001'


# Opening JSON file
json_url = src_json_node + "/" + str(el_pid)
jraw =  requests.get(json_url, auth=basic)
fac_json = jraw.content.decode('utf-8')
# returns JSON object as Dicts
fac_data = json.loads(fac_json)
fac_name = list(fac_data.keys())[0]
fac_model = fac_data[fac_name]
model_data['RCHRES_R001'][fac_name] = fac_model


container = False 

# Add object_class to the run_mode and flow_mode
model_data['RCHRES_R001']['run_mode']['object_class'] = 'ModelConstant'
model_data['RCHRES_R001']['flow_mode']['object_class'] = 'ModelConstant'
model_data['RCHRES_R001']['IVOL']= {
    'object_class' : 'ModelLinkage',
    'right_path' : '/STATE/RCHRES_R001/HYDR/IVOL',
    'name' : 'IVOL',
    'link_type' : 2
}

# call it!
model_loader_recursive(model_data, container)
# this should be done as a lnkage in json:
river = model_object_cache['/STATE/RCHRES_R001']
river.add_input('IVOL', '/STATE/RCHRES_R001/HYDR/IVOL')
run_mode = ModelConstant('run_mode', False, model_data['RCHRES_R001']['run_mode']['value'], '/STATE/run_mode')
flow_mode = ModelConstant('flow_mode', False, model_data['RCHRES_R001']['flow_mode']['value'], '/STATE/flow_mode')

# save the json to a file named after the riverseg
with open("C:/usr/local/home/git/HSPsquared/tests/testcbp/HSP2results/" + river.model_props_parsed['riverseg']['value'] + ".json", "w") as river_file:
    json.dump(model_data, river_file, indent=4, sort_keys=True)



print("Loaded the following objects & paths")
print("Insuring all paths are valid, and connecting models as inputs")
model_path_loader(model_object_cache)
print("Tokenizing models")
model_root_object = model_object_cache["/STATE/RCHRES_R001"]
model_exec_list = []
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)

# step if you like
# make the model_exec_list into a typed Dict (for numba)
# note: this is done in the utilities_specl.py code
model_exec_list = np.asarray(model_exec_list, dtype="i8")
# set up info and timer
siminfo = {}
siminfo['delt'] =3600
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)
# then call the step 
step = 1 
set_state(state_ix, state_paths, '/STATE/RCHRES_R001/HYDR/IVOL', 44.3)
# call to see if it throws an error
step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 1)
# call a flexible, non-jit debug step
test_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
# call just one op token set, but from the step_one() wrapper
step_one(op_tokens, op_tokens[18], state_ix, dict_ix, ts_ix, step, 1)
# call an individual routine with debugging info 
debug_tbl_eval(op_tokens, op_tokens[18], state_ix, dict_ix)