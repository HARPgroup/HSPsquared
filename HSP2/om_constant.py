"""
The class Constant is bare bones, it sets the state variable and value.
However, this is useful to insure consistent handling of constants throughout the simulation architecture.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from numba import njit

# Function for use during model simulations of tokenized objects
# really not needed, and would be more efficient to just return the value 
# and should never actually be called?  but this is what it would look like if it was called
@njit
def step_model_constant(op_token, state_ix, ts_ix, step):
    return state_ix[op_token[1]]

