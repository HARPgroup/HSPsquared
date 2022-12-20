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


def set_state(state_ix, state_paths, var_path, default_value = 0.0):
    """
    Given an hdf5 style path to a variable, set the value 
    If the variable does not yet exist, create it.
    Returns the integer key of the variable in the state_ix Dict
    """
    if not (var_path in state_paths.keys()):
        # we need to add this to the state 
        state_paths[var_path] = append_state(state_ix, default_value)
    var_ix = state_paths[var_path]
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
    return op_tokens, state_paths, state_ix, dict_ix, ts_ix

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
   

from HSP2.om_model_object import ModelObject
from HSP2.om_equation import Equation, exec_eqn
from HSP2.om_model_linkage import ModelLinkage
def load_sim_dicts(op_tokens, state_paths, state_ix, dict_ix, ts_ix):
    river = ModelObject('RCHRES_R001')
    river.op_tokens, river.state_paths, river.state_ix, river.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)
    river.state_path = specl_state_path('RCHRES', 1)
    river.register_path()
    # 
    river.add_input("Qin", f'{river.state_path}/HYDR/IVOL')
    print("State after adding river Qin", state_ix, state_paths)
    # alternative, using TIMESERIES: 
    # river.inputs["Qin"] = ["/TIMESERIES/TS011"]
    # river.add_input("ps_mgd", "/TIMESERIES/TS3000")
    
    facility = ModelObject('facility', river)
    facility.make_state_path()
    facility.register_path()
    
    Qintake = Equation('Qintake', facility, "Qin * 1.21")
    Qintake.make_state_path()
    Qintake.register_path()
    Qintake.tokenize()
    # a flowby
    flowby = Equation('flowby', facility, "Qintake * 0.9")
    flowby.register_path()
    flowby.tokenize()
    # add a withdrawal equation 
    # we use "3.0 + 0.0" because the equation parser fails on a single factor (number of variable)
    # so we have to tweak that.  However, we need to handle constants separately, and also if we see a 
    # single variable equation (such as Qup = Qhydr) we need to rewrite that to a input anhyow for speed
    wd_mgd = Equation('wd_mgd', facility, "3.0 + 0.0")
    wd_mgd.register_path()
    wd_mgd.tokenize() 
    print("Facility inputs", facility.inputs, facility.inputs_ix)
    # add a series of rando equations 
    c=["flowby", "wd_mgd", "Qintake"]
    #for k in range(100):
    for k in range(2):
        eqn = str(25*random.random()) + " * " + c[round((2*random.random()))]
        newq = Equation('eq' + str(k), facility, eqn)
        newq.register_path()
        newq.tokenize()
        newq.add_op_tokens()
    # now connect the wd_mgd back to the river with a direct link.  
    # This is not how we'll do it for most simulations as there may be multiple inputs but will do for now
    hydr = ModelObject('HYDR', river)
    hydr.register_path()
    O1 = ModelLinkage('O1', hydr, wd_mgd.state_path, 2)
    O1.register_path()
    O1.tokenize() 
    # add tokens to the op_tokens Dict
    river.add_op_tokens()
    facility.add_op_tokens()
    Qintake.add_op_tokens()
    flowby.add_op_tokens()
    wd_mgd.add_op_tokens()
    O1.add_op_tokens()
    
    return


@njit
def iterate_models(op_tokens, state_ix, dict_ix, ts_ix, steps):
    checksum = 0.0
    for step in range(steps):
        pre_step_model(op_tokens, state_ix, dict_ix, ts_ix)
        step_model(op_tokens, state_ix, dict_ix, ts_ix, step)
    return checksum

@njit
def pre_step_model(op_tokens, state_ix, dict_ix, ts_ix):
    for i in op_tokens.keys():
        if op_tokens[i][0] == 1:
            return False
        elif op_tokens[i][0] == 2:
            return False
        elif op_tokens[i][0] == 3:
            return False
        elif op_tokens[i][0] == 4:
            return False
        elif op_tokens[i][0] == 5:
            return False
    return

@njit 
def step_model(op_tokens, state_ix, dict_ix, ts_ix, step):
    for i in op_tokens.keys():
        if op_tokens[i][0] == 1:
            state_ix[i] = exec_eqn(op_tokens[i], state_ix)
        elif op_tokens[i][0] == 2:
            state_ix[i] = exec_tbl_eval(op_tokens[i], state_ix, dict_ix)
        elif op_tokens[i][0] == 3:
            step_model_link(op_tokens[i], state_ix, ts_ix, step)
        elif op_tokens[i][0] == 4:
            return False
        elif op_tokens[i][0] == 5:
            return False
    return 
