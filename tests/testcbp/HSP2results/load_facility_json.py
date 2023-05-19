import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd
from pandas import HDFStore, Timestamp, read_hdf, DataFrame, date_range
from pandas.tseries.offsets import Minute
import os
os.chdir("C:/usr/local/home/git/HSPsquared")
from HSP2.utilities_specl import *
from HSP2.SPECL import specl, _specl_
from HSP2.om_model_object import *
from HSP2.om_equation import *
from HSP2.om_data_matrix import *
from HSP2.om_sim_timer import *
from HSP2.om_model_linkage import ModelLinkage, step_model_link
from HSP2.om_model_broadcast import *
import numpy as np
from numba import int8, float32, njit, types
from numba.typed import Dict


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

src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
el_pid = 4828385 # Greenville County New Reservoir: 5356344, CHesdin WTP: 4828385
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
model_shell = {}
model_shell['RCHRES_R001'] = model_data
model_shell['RCHRES_R001']['name'] = 'RCHRES_R001'
model_shell['RCHRES_R001']['object_class'] = 'ModelObject'
model_data = model_shell # just needed to encapsulate the facility for broadcasts to be OK
container = False 
fac_data = model_data['RCHRES_R001']['Greensville County Raw Water Reservoir and Intake:Nottoway River']

# call it!
model_loader_recursive(model_data, container)
print("Loaded the following objects & paths")
print("Insuring all paths are valid, and connecting models as inputs")
model_path_loader(model_object_cache)
print("Tokenizing models")
model_root_object = model_object_cache["/STATE/RCHRES_R001"]
model_exec_list = []
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)
