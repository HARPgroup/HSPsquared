"""
The class Broadcast is used to send and receive data to shared accumulator "channel" and "register".
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.state import *
from HSP2.om import *
from HSP2.om_model_object import *
from HSP2.om_model_linkage import ModelLinkage
from numba import njit
import warnings

class SimpleChannel(ModelObject):
    def __init__(self, name, container = False, model_props = []):
        super(ModelBroadcast, self).__init__(name, container)
        self.model_props_parsed = model_props
        self.optype = 13 # see list in om_model_object.py
        self.parse_model_props(model_props)
        # add basic numeric state variables for outputs
        self.rvars = {'Qin', 'Rin', 'drainage_area', 'area', 'demand'}
        # old method had q_var, then reported it as Qin this can just be a link or constant
        # and therefore handled by constant_or_path()
        self.wvars = {'Qout', 'depth', 'its', 'Storage', 'last_S', 'rejected_demand_mgd', 'rejected_demand_pct'}
        self.r_var_values = {}
    
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        for op_name in self.rvars:
            self.r_var_values[op_name] = self.handle_prop(model_props, op_name), False)
        # handle variables that used a weird convention in old model
        if 'q_var' in model_props:
            self.r_va_values['Qin'] = self.handle_prop(model_props, 'q_var', False)
        return True
    
    def find_paths(self):
        super().find_paths()
        self.paths_found = False # override parent setting until we verify everything
        # handle props array 
        for op_name in self.rvars:
            self.constant_or_path(op_name, self.r_var_values[op_name], False)
        # the above should result in all rvars as inputs, whether constant or variables
        # then, when we tokenize, we just refer to self.inputs['q_var'] to get the ix 
        self.paths_found = True
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        for op_name in self.rvars:
            self.constant_or_path(op_name, self.handle_prop(model_props, op_name), False)
        # the above should result in all rvars as inputs, whether constant or variables
        # then, when we tokenize, we just refer to self.inputs['q_var'] to get the ix 
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime
@njit
def pre_step_simple_channel(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Need to iterate through the destinations (left side) and set to zero 
    # at the beginning of each timestep.
    # Not completed.

def step_simple_channel(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Need to iterate through the destinations (left side) and set to zero 
    # at the beginning of each timestep.
    # Not completed.
