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

# initialize runtime Dicts
op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache = init_sim_dicts()
model_object_cache = {}
# set on object root class for global sharing
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (op_tokens, state_paths, state_ix, dict_ix, model_object_cache)
# set up info and timer
siminfo = {}
siminfo['delt'] =3600
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)




# Manual loading example 
# set up the river container
river = ModelObject('RCHRES_R001')
domain = river.state_path + "/HYDR"
hydr_ix = hydr_get_ix(state_ix, state_paths, domain)
# upon object creation river gets added to state with path "/STATE/RCHRES_R001"
IVOLin = ModelLinkage("IVOLin", river, '/STATE/RCHRES_R001/HYDR/IVOL', 2)
# Prepare for Tribs
# must listen for Qtrib on child.
broadcast_params = []
broadcast_params.append(["Qtrib","Qtrib"])
broadcast_params.append(["trib_area_sqmi","trib_area_sqmi"])
Listen_to_Children = ModelBroadcast("Listen_to_Children", river, 'read', 'hydroObject', 'child', broadcast_params)

# finalize equations for local versus upstream
drainage_area_sqkm = ModelConstant("drainage_area_sqkm",river,"257.0301") # will be set by json file 
drainage_area_sqmi = Equation("drainage_area_sqmi", river, "drainage_area_sqkm * 0.386102") # will be set by json file 
# if local_area_sqmi = drainage_area_sqmi then this is a headwater
local_area_sqmi = ModelConstant("local_area_sqmi", river, "99.2398") # will be set by json file 
Runit = Equation("Runit", river, "IVOLin / drainage_area_sqmi") # will be set by json file 
# for now, this Qup and Runit approximates runoff, later with DSN10 we will split
Qup = Equation('Qup', river, "IVOLin * (local_area_sqmi / drainage_area_sqmi)")
# tribs can override the local inflows 
Qlocal = Equation('Qlocal', river, "Runit * (local_area_sqmi - trib_area_sqmi)")
Qin = Equation('Qin', river, "Qup + Qlocal + Qtrib")


# add a facility
facility = ModelObject('facility', river)
Qintake = Equation('Qintake', facility, "Qin * 1.0")

# load NHD subsheds from file
jfile = open("C:/Workspace/tmp/8567221.json")
model_data = json.load(jfile)
# in future, we may load the whole dang model, but for now 
# this json file has only the trib info 
trib_data = model_data['RCHRES_R001']
model_loader_recursive(trib_data, river)


print("Loaded the following objects/paths:", state_paths)
print("Insuring all paths are valid, and connecting models as inputs")
# now load 
model_path_loader(model_object_cache)

model_root_object = model_object_cache[river.state_path]
# create ordered list and tokenize
model_exec_list = []
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)
model_exec_list = np.asarray(model_exec_list)

# run the model 
#steps = 3
#iterate_models(op_tokens, state_ix, dict_ix, ts_ix, steps)
set_state(state_ix, state_paths, '/STATE/RCHRES_R001/HYDR/IVOL', 44.3)
pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 1)
step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 1)

# can look at all kinds of state variables like this:
# get this variables state 
# since we know this must have a trib:
moc = model_object_cache
trib2 = moc['/STATE/RCHRES_R001/nhd_8567221/nhd_8567219/nhd_8566779'] 
trib2.get_state('local_area_sqmi')
trib2.get_state('Runit')
trib2.get_state('Qin')
trib2.get_state('Qlocal')
trib2.get_state('Qout')
trib2.get_state('Qtrib')
trib2.get_state('trib_area_sqmi')

trsq = model_object_cache[trib2.find_var_path('hydroObject') + "/" + 'trib_area_sqmi']
trsq.get_state()

# if we only know the local short name (like in an equation), we 
# can still find it as the get_state() routine should check through linkages etc to find values
# Ex: get tje trib_area_sqmi value used in the Qlocal equation 
river.get_state('trib_area_sqmi')
# Get Runit from Qlocal equation
river.get_state('Runit')

# 0.4463933228106152
Qlocal.get_state('local_area_sqmi')
# and any object can be used to get the value of any path
Qlocal.get_state('/STATE/RCHRES_R001/local_area_sqmi')
river.get_state('Qtrib')
river.get_state('/STATE/RCHRES_R001/hydroObject/Qtrib')
Trib1.get_state('Qout')

# look at the ops:
Listen_to_Children.linkages
SendToParent.linkages[1].ops
# test the ops
test_model_link(SendToParent.linkages[1].ops, state_ix, ts_ix, 1)
