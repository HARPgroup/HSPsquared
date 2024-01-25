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

state = init_state_dicts()
op_tokens, model_object_cache = init_om_dicts()
state_context_hsp2(state, 'RCHRES', 'R001', 'HYDR')
hydr_init_ix(state['state_ix'], state['state_paths'], state['domain'])
state_paths, state_ix, dict_ix, ts_ix = state['state_paths'], state['state_ix'], state['dict_ix'], state['ts_ix']
# set globals on ModelObject, this makes them persistent throughout all subsequent object instantiation and use
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (
    op_tokens, state_paths, state_ix, dict_ix, model_object_cache
)
state['op_tokens'], state['model_object_cache'] = op_tokens, model_object_cache 

domain = "/STATE/RCHRES_R001/HYDR" # any objects that are connected to this object should be loaded 
# initialize runtime Dicts
model_data = state['model_data']
# set on object root class for global sharing

# set up info and timer
siminfo = {}
siminfo['delt'] =60
#siminfo['tindex'] = date_range("1984-01-01", "2020-12-31", freq=Minute(siminfo['delt']))[1:]
siminfo['tindex'] = date_range("1984-01-01", "2020-12-31", freq=Minute(siminfo['delt']))[1:]

steps = siminfo['steps'] = len(siminfo['tindex'])
model_object_cache = state['model_object_cache']
op_tokens = state['op_tokens']

container = False 
model_root_object = ModelObject("")
# set up the timer as the first element 
timer = SimTimer('timer', model_root_object, siminfo)
model_touch_list = []

# manually populate or load a file of json 
lfile = True
if lfile == True:
    #jfile = open('/WorkSpace/modeling/projects/james_river/rivanna/beaver_hsp2/JL1_6562_6560.json')
    jfile = open('/WorkSpace/modeling/projects/james_river/rivanna/beaver_hsp2/JL1_6560_6440.json')
    model_data = json.load(jfile)
    state['model_data'] = model_data 
    hydr_init_ix(state_ix, state_paths, '/STATE/RCHRES_R001/HYDR')
    # this just forces something to be here for testing
    IVOLin = ModelConstant("IVOLin", container = False, value = 50.0, state_path = '/STATE/RCHRES_R001/HYDR/IVOL')
    # a test of complex versus simple equation
else:
    facility = ModelObject('facility', model_root_object)
    model_data['RCHRES_R001']['run_mode']['object_class'] = 'ModelConstant'
    model_data['RCHRES_R001']['flow_mode']['object_class'] = 'ModelConstant'
    model_data['RCHRES_R001']['IVOL']= {
        'object_class' : 'ModelLinkage',
        'right_path' : '/STATE/RCHRES_R001/HYDR/IVOL',
        'name' : 'IVOL',
        'link_type' : 2
    }
    c=["flowby", "wd_mgd", "Qintake"]
    flowby = Equation('flowby', facility, {'equation':'10.0'} )
    wd_mgd = Equation('wd_mgd', facility, {'equation':'2.5'} )
    Qintake = Equation('Qintake', facility, {'equation':'50.0'} )
    for k in range(1000):
        eqn = str(25*random.random()) + " * " + c[round((2*random.random()))]
        newq = Equation('eq' + str(k), facility, {'equation':eqn} )
        eqn = 50.0*random.random()
        newq = ModelConstant('con' + str(k), facility, eqn)

# add a handful of helpful objects
model_loader_recursive(state['model_data'], model_root_object)
Qmulti = Equation("Qmulti", model_object_cache['/STATE/RCHRES_R001'], {'equation':'1.0 * Qin * (1.0 + 0.0 * 11.5) / 1.0'} )
Qout = model_object_cache[Qmulti.find_var_path('Qout')]

# now instantiate and link objects
# state['model_data'] has alread been prepopulated from json, .py files, hdf5, etc.

print("Loaded objects & paths: insures all paths are valid, connects models as inputs")
# both state['model_object_cache'] and the model_object_cache property of the ModelObject class def 

# will hold a global repo for this data this may be redundant?  They DO point to the same datset?
# since this is a function that accepts state as an argument and these were both set in state_load_dynamics_om
# we can assume they are there and functioning
model_path_loader(model_object_cache)
# len() will be 1 if we only have a simtimer, but > 1 if we have a river being added
model_exec_list = []
# put all objects in token form for fast runtime execution and sort according to dependency order
print("Tokenizing models")
model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list, model_touch_list )
# model_exec_list is the ordered list of component operations
print("model_exec_list:", model_exec_list)
model_exec_list = np.asarray(model_exec_list, dtype="i8") 
# the resulting set of objects is returned.
state['model_object_cache'] = model_object_cache
state['op_tokens'] = ModelObject.op_tokens
state['state_step_om'] = 'disabled'

# if you tell it to report on the step that fails (which you have to do iteratively, proc of elim)
# Test iterate over a single op
select_ops = model_exec_list
#select_ops = np.asarray([Qmulti.ix], dtype="i8") 
#select_ops = np.asarray([Qout.ix], dtype="i8") 
#select_ops = np.asarray([Qmulti.ix, Qout.ix], dtype="i8") 
# does it go faster if we know which ones are runnable and dont try those that are static?
rmeo = ModelObject.runnable_op_list(ModelObject.op_tokens, model_exec_list)
# using onlye these runnables cuts runtime by over 40%
select_ops = rmeo
#siminfo['steps'] = 100000

# Test and time the run
# this is a testing mode for running, the last arg is the step to report exec for each component
# to allow to trace, that is, the last ix that the model reports will be the one that failed 
start = time.time()

iterate_perf(select_ops, op_tokens, state_ix, dict_ix, ts_ix, siminfo['steps'], -1)
#iterate_perf(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 3, -1)
end = time.time()
print(len(select_ops), "components iterated over", siminfo['steps'], "time steps took" , end - start, "seconds")



# if a model fails on a given ix, search for it, for example, (if last ix reported is 234 then:
# get_ix_path(state_paths, 234)
# or direct like so: 
#    model_object_cache['/STATE/facility'].add_op_tokens()
# or 
#    model_object_cache['/STATE/facility/Qintake'].get_state()
# Runit = model_object_cache['/STATE/RCHRES_R001/Runit']
# local_channel = model_object_cache['/STATE/RCHRES_R001/local_channel']
# model_object_cache['/STATE/RCHRES_R001/drainage_area_sqmi'].get_state()
# Runit.get_state()
# even step:
# step_equation(np.asarray(Qintake.ops, dtype="i8"), state_ix)
# can find paths for ested variables like so: search_path(state_paths,'nhd_8566699')
# - use a 3rd argument 'max' if you want the longest matching path, not the shortest. 
# trib = model_object_cache[search_path(state_paths,'nhd_8566699')]
