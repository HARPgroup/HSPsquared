"""
The class SpecialAction is used to support original HSPF ACTIONS.
"""
from HSP2.state import *
from HSP2.om import *
from HSP2.om_model_object import ModelObject
from numba import njit
class FlowBy(ModelObject):
    def __init__(self, name, container = False, model_props = {}):
        super(FlowBy, self).__init__(name, container, model_props)
        self.optype = 15 # Special Actions start indexing at 100 
    
    def parse_model_props(self, model_props, strict=False):
        print("FlowBy.parse_model_props() called")
        super().parse_model_props(model_props, strict)
        # Handle props for a basic flowby
        #   - cfb_condition: eq / lt / gt / lte / gte	 	 
        #   - cfb_var: string (reference input)
        #   - enable_cfb: 0 / 1	
        #   - flowby_eqn: string, will be converted into an equation object	called "flowby" that is an input
        print("Creating ACTION with props", model_props) 
        self.enable_cfb = int(self.handle_prop(model_props, 'enable_cfb', False, 0))
        self.cfb_condition = int(self.handle_prop(model_props, 'cfb_condition'))
        self.cfb_var = self.handle_prop(model_props, 'cfb_var')
        self.flowby_eqn = self.handle_prop(model_props, 'flowby_eqn') # 
        # @todo: handle lookup table types, should be just a child table, anduse the value of the table instead of an equation, OR, use the conditional
        #        will have to see if there are DataMatrix inputs that are renamed in this set and convert appropriately
        # now add the state value that we are operating on (the target) as an input, so that this gets executed AFTER this is set initially
    
    def handle_prop(self, model_props, prop_name, strict = False, default_value = None ):
        # Insure all values are legal ex: no DIV by Zero
        prop_val = super().handle_prop(model_props, prop_name, strict, default_value )
        if (prop_name == 'cfb_var'):
            if (self.enable_cfb > 0 ):
                if self.cfb_var == None:
                    raise Exception("Error: Flowby with CFB enabled must have CFB: " + self.name + " Halting.") 
                else:
                    self.add_input('cfb', self.cfb_var, 1, True)
        if (prop_name == 'equation'):
            eq = Equation('flowby', self, {'equation':self.flowby_eqn})
        if (prop_name == 'cfb_condition'):
            ids = {'lt': 0, 'gt':1}
            if prop_val in lds.keys():
                self.cfb_con_int = lds[prop_val]
            else:
                raise Exception("Error: Non-valid flowby CFB given:" + prop_val + " for " + self.name + " valid values are 'lt' and 'gt'. Halting.") 
        return prop_val

    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize() # sets self.ops = op_type, op_ix
        self.ops = self.ops + [self.inputs_ix['flowby'], self.enable_cfb, self.inputs_ix['cfb'], self.cfb_con_int]
        # @tbd: check if time ops have been set and tokenize accordingly
        print("Flowby", self.name, "tokens", self.ops)
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()


# njit functions for runtime

@njit(cache=True)
def step_flowby(op, state_ix, dict_ix, step):
    ix = op[1] # ID of this op
    # these indices must be adjusted to reflect the number of common op tokens
    # SpecialAction has:
    # - type of condition (+=, -=, ...)
    # - operand 1 (left side)
    # - operand 2 (right side) 
    # @tbd: check if time ops have been set and enable/disable accordingly
    #     - 2 ops will be added for each time matching switch, the state_ix of the time element (year, month, ...) and the state_ix of the constant to match
    #     - matching should be as simple as if (state_ix[tix1] <> state_ix[vtix1]): return state_ix[ix1] (don't modify the value)
    #     - alternative: save the integer timestamp or timestep of the start, and if step/stamp > value, enable
    # @tbd: add number of repeats, and save the value of repeats in a register
    flowby = state_ix[op[3]] # self.ops + [self.enable_cfb, self.inputs_ix['cfb'], self.cfb_con_int]
    enable_cfb = state_ix[op[3]] # 
    cfb_val = state_ix[op[4]]
    cfb_op = state_ix[op[5]]
    # set preliminary value as computed flowby
    result = flowby
    if (enable_cfb == 1):
        if cfb_op == 0:
            if (cfb_val < flowby):
                result = cfb_val
        elif cfb_op == 1:
            if (cfb_val > flowby):
                result = cfb_val
    # set value in state
    state_ix[ix] = result
    return True

