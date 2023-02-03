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

# show the needed props here
DataMatrix.required_properties()
DataMatrix.check_properties(['name'])
DataMatrix.check_properties(['name', 'matrix_vals'])
DataMatrixLookup.check_properties(['name', 'matrix_vals', 'mx_type', 'key1', 'lu_type1', 'key2', 'lu_type2'])

# initialize runtime Dicts
op_tokens, state_paths, state_ix, dict_ix, ts_ix = init_sim_dicts()
loaded_model_objects = {}
# set on object root class for global sharing
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)
# set up info and timer
siminfo = {}
siminfo['delt'] =3600
siminfo['tindex'] = date_range("2001-01-01", "2001-12-31", freq=Minute(siminfo['delt']))[1:]
steps = siminfo['steps'] = len(siminfo['tindex'])
timer = SimTimer('timer', False, siminfo)

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

loaded_model_objects[Qintake.state_path] = Qintake 
model_path_loader(loaded_model_objects)
