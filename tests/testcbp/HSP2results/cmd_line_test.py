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

# show the needed props here
DataMatrix.required_properties()
DataMatrix.check_properties(['name'])
DataMatrix.check_properties(['name', 'matrix_vals'])
DataMatrixLookup.check_properties(['name', 'matrix_vals', 'mx_type', 'key1', 'lu_type1', 'key2', 'lu_type2'])

# initialize runtime Dicts
op_tokens, state_paths, state_ix, dict_ix, ts_ix = init_sim_dicts()
model_object_cache = {}
# set on object root class for global sharing
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)
# set up info and timer
siminfo = {}
siminfo['delt'] =3600
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)


model_object_cache = {}
model_exec_list = {}
container = False 
# call it!
model_loader_recursive(model_data, container, model_object_cache)
print("Loaded the following objects/paths:", state_paths)
print("Insuring all paths are valid, and connecting models as inputs")
model_path_loader(model_object_cache)
print("Tokenizing models")
model_root_object = model_object_cache["/STATE/RCHRES_R001"]
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)

# set up the river container
river = ModelObject('RCHRES_R001')
domain = river.state_path + "/HYDR"
hydr_ix = hydr_get_ix(state_ix, state_paths, domain)

# upon object creation river gets added to state with path "/STATE/RCHRES_R001"
Qin = ModelLinkage("Qin", river, '/STATE/RCHRES_R001/HYDR/IVOL', 2)
Qup = ModelLinkage("Qup", river, '/STATE/RCHRES_R001/HYDR/IVOL', 2)

facility = ModelObject('facility', river)

Qintake = Equation('Qintake', facility, "Qin * 1.0")

# Test new routine
Qintake.find_paths()

# blank it out to test find_var_path()
Qintake.inputs = {}
Qintake.find_var_path('Qup')
Qintake.constant_or_path('Qup', 'Qup')

# Prepare for Tribs
Qin1 = Equation('Qin1', facility, "Qtrib + Qlocal + Qup")
IVOLin = ModelLinkage("IVOLin", river, '/STATE/RCHRES_R001/HYDR/IVOL', 2)
drainage_area_sqkm = Equation("drainage_area_sqkm",river,"257.0301") # will be set by json file 
drainage_area_sqmi = Equation("drainage_area_sqmi", river, "drainage_area_sqkm * 0.386102") # will be set by json file 
Runit = Equation("Runit", river, "IVOLin / drainage_area_sqmi") # will be set by json file 
# Trib 1 
Trib1 = ModelObject("Trib1", river)
Trib1_da = Equation('drainage_area_sqmi', Trib1, "0.386102 * 5.0")
Qin_trib1 = Equation('Qin', Trib1, "drainage_area_sqmi * Runit")
# test a broadcast element
broadcast_params = []
broadcast_params.append(["Qout","Qtrib"])
broadcast_params.append(["drainage_area_sqmi","trib_area_sqmi"])
SendToParent = ModelBroadcast("Send_to_Parent", Trib1, 'send', 'hydroObject', 'parent', broadcast_params)


model_object_cache[Qintake.state_path] = Qintake 
model_path_loader(model_object_cache)
