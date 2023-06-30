import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd
from pandas import HDFStore, Timestamp, read_hdf, DataFrame, date_range
from pandas.tseries.offsets import Minute
import os
os.chdir("C:/usr/local/home/git/HSPsquared")
from HSP2.state import *
from HSP2.om import *
from HSP2.SPECL import specl
from HSP2.om_model_object import *
from HSP2.om_equation import *
from HSP2.om_data_matrix import *
from HSP2.om_sim_timer import *
from HSP2.om_model_linkage import ModelLinkage, step_model_link
from HSP2.om_model_broadcast import *

siminfo = {}
siminfo['delt'] =3600
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)
state = init_state_dicts()

op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache = init_sim_dicts()
model_object_cache = {}
# set on object root class for global sharing
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (op_tokens, state_paths, state_ix, dict_ix, model_object_cache)

# set up info and timer
river = ModelObject('RCHRES_R001')
domain = river.state_path + "/HYDR"
hydr_init_ix(state_ix, state_paths, domain)
hydr_ix = hydr_get_ix(state_ix, state_paths, domain)
# upon object creation river gets added to state with path "/STATE/RCHRES_R001"
IVOLin = ModelLinkage("IVOLin", river, '/STATE/RCHRES_R001/HYDR/IVOL', 2)
# add a facility
facility = ModelObject('facility', river)
Qin = Equation('Qin', facility, "1.0 * IVOLin")
Qintake = Equation('Qintake', facility, "Qin * 1.0")

model_root_object = river

# now resolve all paths in model objects
print("Loading objects & paths: insures all paths are valid, connects models as inputs")
model_path_loader(model_object_cache)
# len() will be 1 if we only have a simtimer, but > 1 if we have a river being added
print("Tokenizing models")
model_exec_list = []
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)
print("model_exec_list:", model_exec_list)
# not sure if this still is needed?  Maybe it is used to stash the model_exec_list?
op_tokens[0] = np.asarray(model_exec_list, dtype="i8") 
# the resulting set of objects is returned.
state['model_object_cache'] = model_object_cache
state['op_tokens'] = op_tokens
if len(op_tokens) > 0:
    siminfo['state_step_om'] = True 
return