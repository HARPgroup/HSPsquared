"""
The class SpecialAction is used to support original HSPF ACTIONS.
Draft: @tbd: 
        - CTCODE: code specifying time units of the interval between separate applications or actions -
                (valid values: MI,HR,DY,MO,YR)
        - CDEFFG: deferral flag - indicates how to treat deferral of the action under a conditional situation - 
                (valid values: SKIP, SHIFT, ACCUM; default = SKIP)
        - FRACT: fractions for each of the separate applications

"""
import numpy as np
from numba import njit

from hsp2.hsp2.om import is_float_digit
from hsp2.hsp2.om_model_object import ModelObject

class Conditional(ModelObject):
    def __init__(self, name, container = False, model_props = None):
        if model_props is None:
            model_props = {}
        super(SpecialAction, self).__init__(name, container, model_props)

        self.optype = 100 # Special Actions start indexing at 100 
    
    def parse_model_props(self, model_props, strict=False):
        super().parse_model_props(model_props, strict)
        # comes in as row from special CONDITIONAL table
        self.arg1 = self.handle_prop(model_props, 'ARG1')
        self.op_type = self.handle_prop(model_props, 'OP')
        self.arg2 = self.handle_prop(model_props, 'ARG2')
        self.arg1_ix = self.constant_or_path('arg1', self.arg1) # constant values must be added to STATE and thus are referenced by their state_ix number
        self.arg2_ix = self.constant_or_path('arg2', self.arg1) # constant values must be added to STATE and thus are referenced by their state_ix number
    
    def handle_prop(self, model_props, prop_name, strict = False, default_value = None ):
        # Insure all values are legal ex: no DIV by Zero
        prop_val = super().handle_prop(model_props, prop_name, strict, default_value )
        if (prop_name == 'VALUE') and (self.ac == '/='):
            if (prop_val == 0) or (prop_val == None):
                raise Exception("Error: in properties passed to "+ self.name + " AC must be non-zero or non-Null .  Object creation halted. Path to object with error is " + self.state_path)
        if (prop_name == 'op_type'):
           self.handle_op_type(prop_val)
        return prop_val
    
    def handle_ac(self, ac):
        # cop_code 0: =/eq, 1: </lt, 2: >/gt, 3: <=/le, 4: >=/ge, 5: <>/ne 
        cop_codes = {
            '=': 1,
            '+=': 2,
            '<=': 3,
            '<>': 4
        }
        # these codes could be stored in a state_char but that would be slow for little reason
        if not (is_float_digit(ac)):
            if not (ac in cop_codes.keys()):
               raise Exception("Error: in "+ self.name + " AC (" + ac + ") not supported.  Object creation halted. Path to object with error is " + self.state_path)
            opid = cop_codes[ac]
            self.ac = ac
        else:
            # this will fail catastrophically if the requested function is not supported
            # which is a good thing
            if not (ac in cop_codes.values()):
               raise Exception("Error: in "+ self.name + "numeric AC (" + ac + ") not supported.  Object creation halted. Path to object with error is " + self.state_path)
            opid = ac
            self.ac = list(cop_codes.keys())[list(cop_codes.values()).index(ac) ]
        self.opid = opid

    def tokenize(self):
        # NOT YET COMPLETE FOR THIS METHOD THESE ARE COPIED FROM THE BASE SPECIAL ACTION CLASS
        # call parent method to set basic ops common to all 
        super().tokenize() # sets self.ops = op_type, op_ix
        self.ops = self.ops + [self.op1_ix, self.opid, self.op2_ix, self.timer_ix, self.ctr_ix, self.num]
        # @tbd: check if time ops have been set and tokenize accordingly
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()


# njit functions for runtime

@njit(cache=True)
def step_conditional(op, state_ix, dict_ix, step):
    ix = op[1] # ID of this op
    a_id = op[2] # the state ID of any conditional that owns this - can we have nested special actuons?
    if (state_ix[a_id] == 0):
        state_ix[ix] = 0 # this gets disabled too
        return
    
    ix1 = op[2] # ID of source of data and destination of data
    sop = op[3]
    ix2 = op[4]
    result = 0
    if sop == 1:
        if state_ix[ix1] > state_ix[ix2]:
            result = 1
    elif sop == 2:
        if state_ix[ix1] < state_ix[ix2]:
            result = 1
    elif sop == 3:
        if state_ix[ix1] == state_ix[ix2]:
            result = 1
    elif sop == 4:
        if state_ix[ix1] != state_ix[ix2]:
            result = 1
    
    state_ix[ix] = result
    return result

