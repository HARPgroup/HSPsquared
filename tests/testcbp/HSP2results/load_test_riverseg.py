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
Qup = Equation('Qup', river, "IVOLin * (drainage_area_sqmi - local_area_sqmi) / drainage_area_sqmi")
# tribs can override the local inflows 
Qlocal = Equation('Qlocal', river, "Runit * (local_area_sqmi - trib_area_sqmi)")
Qin = Equation('Qin', river, "Qup + Qlocal + Qtrib")


# add a facility
facility = ModelObject('facility', river)
Qintake = Equation('Qintake', facility, "Qin * 1.0")
hydr = ModelObject('HYDR', river)
#O1 = ModelLinkage('O1', hydr, wd_mgd.state_path, 2)
# because we may not be able to determine the difference with non-lagged tribs 
#IVOLtest = ModelLinkage('IVOLtest', hydr, Qin.state_path, 2)
#IVOL = ModelLinkage('IVOL', hydr, Qin.state_path, 2)