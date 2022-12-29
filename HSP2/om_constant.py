"""
The class Constant is bare bones, it sets the state variable and value.
However, this is useful to insure consistent handling of constants throughout the simulation architecture.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from numba import njit


class Constant(ModelObject):
    def __init__(self, name, container = False, value = 0.0):
        super(Constant, self).__init__(name, container)
        self.optype = 7 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - Constant (numeric)
        self.default_value = value 
        self.register_path() #this is one of the few that register a path by default since there are no contingencies to await
        #set_state(self.state_ix, self.state_paths, self.state_path, self.default_value)
        self.state_ix[self.ix] = self.default_value

# Function for use during model simulations of tokenized objects
# really not needed, and would be more efficient to just return the value 
# and should never actually be called?  but this is what it would look like if it was called
@njit
def step_model_constant(op_token, state_ix, ts_ix, step):
    return state_ix[op_token[1]]

