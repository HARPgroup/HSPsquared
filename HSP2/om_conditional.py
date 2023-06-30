"""
The class Conditional is used to translate provide table lookup and interpolation function.
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.state import *
from HSP2.om import *
from HSP2.om_model_object import ModelObject
from numba import njit
class Conditional(ModelObject):
    def __init__(self, name, container = False, matrix_vals = []):
        super(DataMatrix, self).__init__(name, container, left_side, cop, right_side)
        self.left_side = left_side
        self.cop = cop
        self.right_side = right_side
        self.optype = 2 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        # cop_code 0: =/eq, 1: </lt, 2: >/gt, 3: <=/le, 4: >=/ge, 5: <>/ne 
        cop_codes = [
            '=': 0,
            'eq': 0,
            'lt': 1,
            '<': 1,
            'gt': 2,
            '>': 2,
            '<=': 3,
            'le': 3,
            '>=': 4,
            'ge': 4,
            '<>': 5,
            'ne': 5
        ]
        self.ops = self.ops + [self.left_ix, cop_codes[self.cop], self.right_ix]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime

@njit
def exec_conditional(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # these indices must be adjusted to reflect the number of common op tokens
    # Conditional has:
    # - type of condition (>, <, ...)
    # - operand 1 (left side)
    # - operand 2 (right side)
    # - ix of value if left side
    # - ix of value if right side 
    op = op[3] # not used yet, what type of table?  in past this was always 1-d or 2-d 
    op1 = op[4]
    op2 = op[5]
    ix1 = op[6]
    ix2 = op[7]
    if op == 0:
      if op1 > op2:
        result = state_ix[ix1]
      else:
        result = state_ix[ix2]
    if op == 1:
      if op1 < op2:
        result = state_ix[ix1]
      else:
        result = state_ix[ix2]
        
    return result

