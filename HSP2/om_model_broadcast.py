"""
The class Broadcast is used to send and receive data to shared accumulator "channel" and "register".
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.om_model_object import ModelObject
from HSP2.om_model_object import ModelLinkage
from HSP2.utilities_specl import *
from numba import njit
class ModelBroadcast(ModelObject):
    def __init__(self, name, container = False, broadcast_type = 'read', broadcast_params = [], broadcast_channel = False):
        super(ModelObject, self).__init__(name, container)
        # broadcast_params = [ [local_name1, remote_name1], [local_name2, remote_name2], ...]
        # broadcast_channel = state_path/[broadcast_channel]
        self.linkages = {} # store of objects created by this  
        self.broadcast_type = broadcast_type
        local_path = # the recipient of the broadcast data 
        for i in broadcast_params.keys():
            # create an object for each element in the array 
            if (broadcast_type == 'read'):
                # create a link object of type 2, property reader to local state 
                self.linkages[i] = ModelLinkage(broadcast_params[i][0], container, broadcast_params[i][1], 2)
                bc_type_id = 0
            else:
                # TBD
                # push a value onto an accumulator 
                # need path to receiver object + broadcast_channel + remote name 
                receiver = False # to be done                 
                self.linkages[i] = ModelLinkage(broadcast_params[i][0], container, hub_path + broadcast_params[i][1], 2)
                bc_type_id = 1 
        self.optype = 4 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
        self.bc_type_id = bc_type_id
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        if (self.broadcast_type == 'send'):
            for i in self.linkages.keys():
                self.ops = self.ops + [self.left_ix, cop_codes[self.cop], self.right_ix]
        else:
            # this is a read, so we simply rewrite as a model linkage 
            self.linkage.tokenize()
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime

@njit
def pre_step_broadcast(op, state_ix, dict_ix):
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

