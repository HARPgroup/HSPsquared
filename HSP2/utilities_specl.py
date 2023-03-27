''' General routines for SPECL '''

import numpy as np
import time
from numba.typed import Dict
from numpy import zeros
from numba import int8, float32, njit, types, typed # import the types
import random # this is only used for a demo so may be deprecated

def find_state_path(state_paths, parent_path, varname):
    """
    We should get really good at using docstrings...
    """
    # this is a bandaid, we should have an object routine that searches the parent for variables or inputs
    var_path = parent_path + "/states/" + str(varname)
    return var_path


def get_state_ix(state_ix, state_paths, var_path):
    """
    Find the integer key of a variable name in state_ix 
    """
    if not (var_path in list(state_paths.keys())):
        # we need to add this to the state 
        return False # should throw an error 
    var_ix = state_paths[var_path]
    return var_ix


def get_ix_path(state_paths, var_ix):
    """
    Find the integer key of a variable name in state_ix 
    """
    for spath, ix in state_paths.items():
        if var_ix == ix:
            # we need to add this to the state 
            return spath 
    return False


def get_exec_order(model_exec_list, var_ix):
    """
    Find the integer key of a variable name in state_ix 
    """
    model_exec_list = dict(enumerate(model_exec_list.flatten(), 1))
    for exec_order, ix in model_exec_list.items():
        if var_ix == ix:
            # we need to add this to the state 
            return exec_order 
    return False

def set_state(state_ix, state_paths, var_path, default_value = 0.0, debug = False):
    """
    Given an hdf5 style path to a variable, set the value 
    If the variable does not yet exist, create it.
    Returns the integer key of the variable in the state_ix Dict
    """
    if not (var_path in state_paths.keys()):
        # we need to add this to the state 
        state_paths[var_path] = append_state(state_ix, default_value)
    var_ix = get_state_ix(state_ix, state_paths, var_path)
    if (debug == True):
        print("Setting state_ix[", var_ix, "], to", default_value)
    state_ix[var_ix] = default_value
    return var_ix


def set_dict_state(state_ix, dict_ix, state_paths, var_path, default_value = {}):
    """
    Given an hdf5 style path to a variable, set the value in the dict
    If the variable does not yet exist, create it.
    Returns the integer key of the variable in the state_ix Dict
    """
    if not (var_path in state_paths.keys()):
        # we need to add this to the state 
        state_paths[var_path] = append_state(state_ix, default_value)
    var_ix = get_state_ix(state_ix, state_paths, var_path)
    return var_ix


def append_state(state_ix, var_value):
    """
    Add a new variable on the end of the state_ix Dict
    Return the key of this new variable
    """
    if (len(state_ix) == 0):
      val_ix = 1
    else:
        val_ix = max(state_ix.keys()) + 1 # next ix value
    state_ix[val_ix] = var_value
    return val_ix


def init_op_tokens(op_tokens, tops, eq_ix):
    """
    Iinitialize the op_tokens Dict
    This contains the runtime op code for every dynamic operation to be used
    """
    for j in range(len(tops)):
        if isinstance(tops[j], str):
            # must add this to the state array as a constant
            s_ix = append_state(state_ix, float(tops[j]))
            tops[j] = s_ix
    
    op_tokens[eq_ix] = np.asarray(tops, dtype="i8")

def is_float_digit(n: str) -> bool:
    """
    Helper Function to determine if a variable is numeric
    """
    try:
        float(n)
        return True
    except ValueError:
        return False

@njit 
def exec_op_tokens(op_tokens, state_ix, dict_ix, steps):
    """
    We should get really good at using docstrings...
    """
    checksum = 0.0
    for step in range(steps):
        for i in op_tokens.keys():
            s_ix = op_tokens[i][1] # index of state for this component
            if op_tokens[i][0] == 1:
                state_ix[s_ix] = exec_eqn_nall_m(op_tokens[i], state_ix)
            elif op_tokens[i][0] == 2:
                state_ix[s_ix] = exec_tbl_eval(op_tokens[i], state_ix, dict_ix)
            checksum += state_ix[i]
    return checksum


@njit
def exec_eqn_nall_m(op_token, state_ix):
    """
    We should get really good at using docstrings...
    """
    op_class = op_token[0] # we actually will use this in the calling function, which will decide what 
                      # next level function to use 
    result = 0
    num_ops = op_token[2]
    s = np.array([0.0])
    s_ix = -1 # pointer to the top of the stack
    s_len = 1
    #print(num_ops, " operations")
    # todo: the default is to iterate through all pairs, however, we could identify known forms
    #       such as (x * y) / z 
    #       and whenever that opcode sequence occurs, we could do the eval in a single step, cutting ops in half
    #       more complex forms with 4 or 5 ops could have even more time savings.    
    for i in range(num_ops): 
        op = op_token[3 + 3*i]
        t1 = op_token[3 + 3*i + 1]
        t2 = op_token[3 + 3*i + 2]
        # if val1 or val2 are < 0 this means they are to come from the stack
        # if token is negative, means we need to use a stack value
        #print("s", s)
        if t1 < 0: 
            val1 = s[s_ix]
            s_ix -= 1
        else:
            val1 = state_ix[t1]
        if t2 < 0: 
            val2 = s[s_ix]
            s_ix -= 1
        else:
            val2 = state_ix[t2]
        #print(s_ix, op, val1, val2)
        if op == 1:
            #print(val1, " - ", val2)
            result = val1 - val2
        elif op == 2:
            #print(val1, " + ", val2)
            result = val1 + val2
        elif op == 3:
            #print(val1, " * ", val2)
            result = val1 * val2 
        elif op == 4:
            #print(val1, " / ", val2)
            result = val1 / val2 
        elif op == 5:
            #print(val1, " ^ ", val2)
            result = pow(val1, val2) 
        s_ix += 1
        if s_ix >= s_len: 
            s = np.append(s, 0)
            s_len += 1
        s[s_ix] = result
    result = s[s_ix]
    return result 

def init_sim_dicts():
    """
    We should get really good at using docstrings...
    Agree. they are dope.
    """
    op_tokens = Dict.empty(key_type=types.int64, value_type=types.i8[:])
    state_paths = Dict.empty(key_type=types.unicode_type, value_type=types.int64)
    state_ix = Dict.empty(key_type=types.int64, value_type=types.float64)
    dict_ix = Dict.empty(key_type=types.int64, value_type=types.float64[:,:])
    ts_ix = Dict.empty(key_type=types.int64, value_type=types.float64[:])
    model_object_cache = {} # this does not need to be a special Dict as it is not used in numba 
    return op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache

def hydr_get_ix(state_ix, state_paths, domain):
    # get a list of keys for all hydr state variables
    hydr_state = ["DEP","IVOL","O1","O2","O3","OVOL1","OVOL2","OVOL3","PRSUPY","RO","ROVOL","SAREA","TAU","USTAR","VOL","VOLEV"]
    hydr_ix = Dict.empty(key_type=types.unicode_type, value_type=types.int64)
    for i in hydr_state:
        #var_path = f'{domain}/{i}'
        var_path = domain + "/" + i
        hydr_ix[i] = set_state(state_ix, state_paths, var_path, 0.0)
    return hydr_ix    

 
def op_path_name(operation, id):
    tid = str(id).zfill(3)
    path_name = f'{operation}_{operation[0]}{tid}'
    return path_name

def specl_state_path(operation, id, activity = ''):
    op_name = op_path_name(operation, id) 
    if activity == '':
        op_path = f'/STATE/{op_name}'
    else:
        op_path = f'/STATE/{op_name}/{activity}'
    return op_path

# set up libraries to import for the load_sim_dicts function
# later, this will be drawing from the hdf5, but for now we 
# are hard-wiring a set of components for testing.
# Note: these import calls must be done down here AFTER the helper functions
#       defined aove that are called by the object classes
from HSP2.om_model_object import *
from HSP2.om_sim_timer import *
from HSP2.om_equation import *
from HSP2.om_model_linkage import *
from HSP2.om_data_matrix import *
from HSP2.om_model_broadcast import *
from HSP2.utilities import versions, get_timeseries, expand_timeseries_names, save_timeseries, get_gener_timeseries

def load_sim_dicts(siminfo, op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache):
    # by setting the state_parhs, opt_tokens, state_ix etc on the abstract class ModelObject
    # all objects that we create share this as a global referenced variable.  
    # this may be a good thing or it may be bad?  For now, we leverage this to reduce settings props
    # but at some point we move all prop setting into a function and this maybe doesn't seem so desirable
    # since there could be some unintended consequences if we actually *wanted* them to have separate copies
    # tho since the idea is that they are global registries, maybe that is not a valid concern.
    ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (op_tokens, state_paths, state_ix, dict_ix, model_object_cache)
    # set up the timer as the first element 
    timer = SimTimer('timer', False, siminfo)
    timer.add_op_tokens()
    river = ModelObject('RCHRES_R001')
    # upon object creation river gets added to state with path "/STATE/RCHRES_R001"
    river.add_input("Qin", f'{river.state_path}/HYDR/IVOL', 2)
    # alternative, using TIMESERIES: 
    # river.add_input("Qin", "/TIMESERIES/TS011", 3)
    # river.add_input("ps_mgd", "/TIMESERIES/TS3000", 3)
    river.add_op_tokens() # formally adds this to the simulation
    
    # now add a simple table 
    data_table = np.asarray([ [ 0.0, 5.0, 10.0], [10.0, 15.0, 20.0], [20.0, 25.0, 30.0], [30.0, 35.0, 40.0] ], dtype= "float32")
    dm = DataMatrix('dm', river, data_table)
    dm.add_op_tokens()
    # 2d lookup
    dma = DataMatrixLookup('dma', river, dm.state_path, 2, 17.5, 1, 6.8, 1, 0.0)
    dma.add_op_tokens()
    # 1.5d lookup
    #dma = DataMatrixLookup('dma', river, dm.state_path, 3, 17.5, 1, 1, 1, 0.0)
    #dma.add_op_tokens()
    
    facility = ModelObject('facility', river)
    
    Qintake = Equation('Qintake', facility, "Qin * 1.0")
    Qintake.add_op_tokens()
    # a flowby
    flowby = Equation('flowby', facility, "Qintake * 0.9")
    flowby.add_op_tokens()
    # add a withdrawal equation 
    # we use "3.0 + 0.0" because the equation parser fails on a single factor (number of variable)
    # so we have to tweak that.  However, we need to handle constants separately, and also if we see a 
    # single variable equation (such as Qup = Qhydr) we need to rewrite that to a input anyhow for speed
    wd_mgd = Equation('wd_mgd', facility, "3.0 + 0.0")
    wd_mgd.add_op_tokens() 
    # Runit - unit area runoff
    Runit = Equation('Runit', facility, "Qin / 592.717")
    Runit.add_op_tokens()
    # add local subwatersheds to test scalability
    """
    for k in range(10):
        subshed_name = 'sw' + str(k)
        upstream_name = 'sw' + str(k-1)
        Qout_eqn = str(25*random.random()) + " * Runit "
        if k > 0:
            Qout_eqn = Qout_eqn + " + " + upstream_name + "_Qout"
        Qout_ss = Equation(subshed_name + "_Qout", facility, eqn)
        Qout_ss.add_op_tokens()
    # now add the output of the final tributary to the inflow to this one
    Qtotal = Equation("Qtotal", facility, "Qin + " + Qout_ss.name)
    Qtotal.tokenize()
    """
    # add random ops to test scalability
    # add a series of rando equations 
    """
    c=["flowby", "wd_mgd", "Qintake"]
    for k in range(10000):
        eqn = str(25*random.random()) + " * " + c[round((2*random.random()))]
        newq = Equation('eq' + str(k), facility, eqn)
        newq.add_op_tokens()
    """
    # now connect the wd_mgd back to the river with a direct link.  
    # This is not how we'll do it for most simulations as there may be multiple inputs but will do for now
    hydr = ModelObject('HYDR', river)
    hydr.add_op_tokens()
    O1 = ModelLinkage('O1', hydr, wd_mgd.state_path, 2)
    O1.add_op_tokens()
    
    return

import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd

def load_nhd_simple(siminfo, op_tokens, state_paths, state_ix, dict_ix, ts_ix, model_object_cache):
    # set globals on ModelObject
    ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix, ModelObject.model_object_cache = (op_tokens, state_paths, state_ix, dict_ix, model_object_cache)
    # set up the timer as the first element 
    timer = SimTimer('timer', False, siminfo)
    #timer.add_op_tokens()
    #river = ModelObject('RCHRES_R001')
    # upon object creation river gets added to state with path "/STATE/RCHRES_R001"
    #river.add_input("Qivol", f'{river.state_path}/HYDR/IVOL', 2, True)
    # a json NHD from R parser
    # Opening JSON file
    # load the json data from a pre-generated json file on github
    json_url = "https://raw.githubusercontent.com/HARPgroup/vahydro/master/R/modeling/nhd/nhd_simple_8566737.json"
    # Opening JSON file
    jraw =  requests.get(json_url, verify=False)
    model_json = jraw.content.decode('utf-8')
    # returns JSON object as Dict
    model_data = json.loads(model_json)
    print("Loaded json with keys:", model_data.keys())
    # local file option:
    #jfile = open("C:/usr/local/home/git/vahydro/R/modeling/nhd/nhd_simple_8566737.json")
    #model_data = json.load(jfile)
    # returns JSON object as Dict
    model_exec_list = np.asarray({})
    #model_exec_list = Dict.empty(key_type=types.int64, value_type=types.i8[:])
    container = False 
    # call it!
    model_loader_recursive(model_data, container)
    print("Loaded the following objects/paths:", state_paths)
    print("Insuring all paths are valid, and connecting models as inputs")
    model_path_loader(model_object_cache)
    print("Tokenizing models")
    model_root_object = model_object_cache["/STATE/RCHRES_R001"]
    model_tokenizer_recursive(model_root_object, model_object_cache, model_exec_list)
    return

# model class reader
# get model class  to guess object type in this lib 
# the parent object must be known
def model_class_loader(model_name, model_props, container = False):
    # todo: check first to see if the model_name is an attribute on the container
    # Use: if hasattr(container, model_name):
    # if so, we set the value on the container, if not, we create a new subcomp on the container 
    if model_props == None:
        return False
    if type(model_props) is str:
        if is_float_digit(model_props):
            model_object = ModelConstant(model_name, container, float(model_props) )
            return model_object
        else:
            return False
    elif type(model_props) is dict:
      object_class = model_props.get('object_class')
      if object_class == None:
          # return as this is likely an attribute that is used for the containing class as attribute 
          # and is handled by the container 
          # todo: we may want to handle this here?  Or should this be a method on the class?
          # Use: if hasattr(container, model_name):
          return False
      model_object = False
      # Note: this routine uses the ".get()" method of the dict class type 
      #       for attributes to pass in. 
      #       ".get()" will return NoValue if it does not exist or the value. 
      if object_class == 'Equation':
          eqn = model_props.get('equation')
          if type(eqn) is str:
              eqn_str = eqn
          else:
              if eqn == None:
                  # try for equation stored as normal propcode
                  eqn_str = model_props.get('value')
              else:
                  eqn_str = eqn.get('value')
          if eqn_str == None:
              raise Exception("This object", container.name, "does not have a parent container. Broadcast creation halted. ")
              return False
          model_object = Equation(model_props.get('name'), container, eqn_str )
          #remove_used_keys(model_props, 
      elif object_class == 'Constant':
          model_object = ModelConstant(model_props.get('name'), container, model_props.get('value') )
      elif object_class == 'DataMatrix':
          # add a matrix with the data, then add a matrix accessor for each required variable 
          has_props = DataMatrix.check_properties(model_props)
          if has_props == False:
              print("Matrix object must have", DataMatrix.required_properties())
              return False
          # create it
          model_object = DataMatrix(model_props.get('name'), container, model_props)
      elif object_class == 'ModelBroadcast':
          # add a matrix with the data, then add a matrix accessor for each required variable 
          print("Loading ModelBroadcast class ")
          has_props = ModelBroadcast.check_properties(model_props)
          if has_props == False:
              print("ModelBroadcast object must have", ModelBroadcast.required_properties())
              return False
          # create it
          broadcast_type = model_props.get('broadcast_type')
          broadcast_channel = model_props.get('broadcast_channel')
          broadcast_hub = model_props.get('broadcast_hub')
          broadcast_params = model_props.get('broadcast_params')
          model_object = ModelBroadcast(model_props.get('name'), container, broadcast_type, broadcast_channel, broadcast_hub, broadcast_params)
      elif object_class == 'MicroWatershedModel':
          # add a matrix with the data, then add a matrix accessor for each required variable 
          has_props = MicroWatershedModel.check_properties(model_props)
          if has_props == False:
              print("MicroWatershedModel object must have", MicroWatershedModel.required_properties())
              return False
          # create it
          model_object = DataMatrix(model_props.get('name'), container, model_props)
          
      elif object_class == 'ModelLinkage':
          right_path = ''
          link_type = False
          left_path = False
          if 'right_path' in model_props.keys():
            right_path = model_props['right_path']
          if 'link_type' in model_props.keys():
            link_type = model_props['link_type']
          if 'left_path' in model_props.keys():
            left_path = model_props['left_path']
          model_object = ModelLinkage(model_props.get('name'), container, right_path, link_type, left_path)
      else:
          model_object = ModelObject(model_props.get('name'), container)
    # one way to insure no class attributes get parsed as sub-comps is:
    # model_object.remove_used_keys() 
    # better yet to just NOT send those attributes as typed object_class arrays, instead just name : value
    return model_object

def model_class_translate(model_props, object_class):
    # make adjustments to non-standard items 
    # this might better be moved to methods on the class handlers
    if object_class == 'hydroImpoundment':
        # special handling of matrix/storage_stage_area column
        # we need to test to see if the storage table has been renamed 
        # make table from matrix or storage_stage_area
        # then make accessors from 
        storage_stage_area = model_props.get('storage_stage_area')
        matrix = model_props.get('matrix')
        if ( (storage_stage_area == None) and (matrix != None)): 
            model_props['storage_stage_area'] = matrix
            del model_props['matrix']

def model_loader_recursive(model_data, container):
    k_list = model_data.keys()
    object_names = dict.fromkeys(k_list , 1)
    if type(object_names) is not dict:
        return False 
    for object_name in object_names:
        #print("Handling", object_name)
        if object_name in {'name', 'object_class', 'id', 'value', 'default'}:
            # we should ask the class what properties are part of the class and also skips these
            # therefore, we can assume that anything else must be a child object that needs to 
            # be handled first -- but how to do this?
            continue
        model_props = model_data[object_name]
        if type(model_props) is not dict:
            # this is a constant, the loader  is built to handle this, but this causes errors with 
            # properties on the class that are expected so we just skip and trust that all constants
            # are formally declared as type Constant
            continue
        if type(model_props) is dict:
            if not ('object_class' in model_props):
                # this is either a class attribute or an un-handleable meta-data 
                # if the class atttribute exists, we should pass it to container to load 
                #print("Skipping un-typed", object_name)
                continue
            #print("Translating", object_name)
            # this is a kludge, but can be important 
            object_class = model_props['object_class']
            model_class_translate(model_props, object_class)
        # now we either have a constant (key and value), or a 
        # fully defined object.  Either one should work OK.
        #print("Trying to load", object_name)
        model_object = model_class_loader(object_name, model_props, container)
        if model_object == False:
            print("Could not load", object_name)
            continue # not handled, but for now we will continue, tho later we should bail?
        # now for container type objects, go through its properties and handle
        if type(model_props) is dict:
            model_loader_recursive(model_props, model_object)

def model_path_loader(model_object_cache):
    k_list = model_object_cache.keys()
    model_names = dict.fromkeys(k_list , 1)
    for model_name in model_names:
        print("Loading paths for", model_name)
        model_object = model_object_cache[model_name]
        model_object.find_paths()


def model_tokenizer_recursive(model_object, model_object_cache, model_exec_list, model_touch_list = []):
    """
    Given a root model_object, trace the inputs to load things in order
    Store this order in model_exec_list
    Note: All ordering is as-needed organic, except Broadcasts
          - read from children is completed after all other inputs 
          - read from parent is completed before all other inputs 
          - could this be accomplished by more sophisticated handling of read 
            broadcasts?  
            - When loading a read broadcast, can we iterate through items 
            that are sending to that broadcast? 
            - Or is it better to let it as it is, 
    """
    if model_object.ix in model_exec_list:
        return
    if model_object.ix in model_touch_list:
        #print("Already touched", model_object.name, model_object.ix, model_object.state_path)
        return
    # record as having been called, and will ultimately return, to prevent recursions
    model_touch_list.append(model_object.ix)
    k_list = model_object.inputs.keys()
    input_names = dict.fromkeys(k_list , 1)
    if type(input_names) is not dict:
        return 
    # isolate broadcasts, and sort out -- what happens if an equation references a broadcast var?
    # is this a limitation of treating all children as inputs? 
    # alternative, leave broadcasts organic, but load children first?
    # children first, then local sub-comps is old method? old method:
    #   - read parent broadcasts
    #   - get inputs (essentially, linked vars)
    #   - send child broadcasts (will send current step parent reads, last step local proc data)
    #   - execute children
    #   - execute local sub-comps
    for input_name in input_names:
        #print("Checking input", input_name)
        input_path = model_object.inputs[input_name]
        if input_path in model_object_cache.keys():
            input_object = model_object_cache[input_path]
            model_tokenizer_recursive(input_object, model_object_cache, model_exec_list, model_touch_list)
        else:
            if input_path in model_object.state_paths.keys():
                # this is a valid state reference without an object 
                # thus, it is likely part of internals that are manually added 
                # which should be fine.  tho perhaps we should have an object for these too.
                continue
            print("Problem loading input", input_name, "input_path", input_path, "not in model_object_cache.keys()")
            return
    # now after tokenizing all inputs this should be OK to tokenize
    model_object.add_op_tokens()
    model_exec_list = np.append(model_exec_list, model_object.ix)


def save_object_ts(io_manager, siminfo, op_tokens, ts_ix, ts):
    # Decide on using from utilities.py:
    # - save_timeseries(io_manager, ts, savedict, siminfo, saveall, operation, segment, activity, compress=True)
    # Or, skip the save_timeseries wrapper and call write_ts() directly in io.py:
    #  write_ts(self, data_frame:pd.DataFrame, save_columns: List[str], category:Category, operation:Union[str,None]=None, segment:Union[str,None]=None, activity:Union[str,None]=None)
    # see line 317 in utilities.py for use example of write_ts()
    x = 0 # dummy
    return

def load_sim_ts(f, state_ix, ts_ix):
  tsq = f['TIMESERIES/'] # f is the hdf5 file 
  # this code replicates a piece of the function of get_timeseries, and loads the full timeseries into a Dict
  # the dict will be keyed by a simple integer, and have values at the time step only.  The actual time 
  # at that step will be contained in ts_ts 
  ts_tables = list(tsq.keys())
  for i in ts_tables:
      if i == 'SUMMARY': continue # skip this non-numeric table
      var_path = '/TIMESERIES/' + i
      ix = set_state(state_ix, state_paths, var_path, 0.0)
      ts_ix[ix] = np.asarray(tsq[i]['table']['values'], dtype="float32")

@njit
def pre_step_timeseries(state_ix, ts_ix, step):
    for idx in ts_ix.keys():
        state_ix[idx] = ts_ix[idx][step] # the timeseries inputs state get set here. must a special type of object to do this



@njit
def iterate_models(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, steps):
    checksum = 0.0
    for step in range(steps):
        pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
        step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    return checksum

@njit
def pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step):
    for i in model_exec_list:
        if op_tokens[i][0] == 1:
            pass
        elif op_tokens[i][0] == 2:
            pass
        elif op_tokens[i][0] == 3:
            pass
        elif op_tokens[i][0] == 4:
            pass
        elif op_tokens[i][0] == 5:
            pass
        elif op_tokens[i][0] == 11:
            pre_step_register(op_tokens[i], state_ix, dict_ix)
    return

@njit 
def step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step):
    val = 0
    for i in model_exec_list:
        step_one(op_tokens, op_tokens[i], state_ix, dict_ix, ts_ix, step, 0)
    return 

@njit
def step_one(op_tokens, ops, state_ix, dict_ix, ts_ix, step, debug = 0):
    # op_tokens is passed in for ops like matrices that have lookups from other 
    # locations.  All others rely only on ops 
    val = 0
    if debug == 1:
        print("DEBUG: Operator ID", ops[1], "is op type", ops[0])
    if ops[0] == 1:
        state_ix[ops[1]] = exec_eqn(ops, state_ix)
    elif ops[0] == 2:
        if (ops[1] == ops[2]):
            # this insures a matrix with variables in it is up to date 
            # only need to do this if the matrix data and matrix config are on same object
            # otherwise, the matrix data is an input and has already been evaluated
            state_ix[ops[1]] = exec_tbl_values(ops, state_ix, dict_ix)
        if (op_tokens[3] > 0):
            # this evaluates a single value from a matrix if the matrix is configured to do so.
            state_ix[ops[1]] = exec_tbl_eval(op_tokens, ops, state_ix, dict_ix)
    elif ops[0] == 3:
        step_model_link(ops, state_ix, ts_ix, step)
    elif ops[0] == 4:
        val = 0
    elif ops[0] == 5:
        step_sim_timer(ops, state_ix, dict_ix, ts_ix, step)
    elif ops[0] == 9:
        val = 0 
    return 


@njit 
def test_model(op_tokens, state_ix, dict_ix, ts_ix, step):
    val = 0
    for i in op_tokens.keys():
        print(i)
        print(op_tokens[i][0])
        if op_tokens[i][0] == 0:
            state_ix[i] = exec_model_object(op_tokens[i], state_ix, dict_ix)
        elif op_tokens[i][0] == 1:
            state_ix[i] = exec_eqn(op_tokens[i], state_ix)
        elif op_tokens[i][0] == 2:
            state_ix[i] = exec_tbl_values(op_tokens[i], state_ix, dict_ix)
        elif op_tokens[i][0] == 3:
            step_model_link(op_tokens[i], state_ix, ts_ix, step)
        elif op_tokens[i][0] == 4:
            val = 0
        elif op_tokens[i][0] == 5:
            step_sim_timer(op_tokens[i], state_ix, dict_ix, ts_ix, step)
        elif op_tokens[i][0] == 8:
            # since this accesses other table objects, gotta pass the entire op_tokens Dict 
            state_ix[i] = exec_tbl_eval(op_tokens, op_tokens[i], state_ix, dict_ix)
    return 
