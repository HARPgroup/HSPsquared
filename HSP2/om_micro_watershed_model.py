"""
The class Broadcast is used to send and receive data to shared accumulator "channel" and "register".
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.om_model_object import ModelObject
from HSP2.om_model_object import ModelLinkage
from HSP2.utilities_specl import *
from numba import njit
class MicroWatershedModel(ModelObject):
    def __init__(self, name, container = False):
        super(ModelObject, self).__init__(name, container)
        self.optype = 9 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - ModelConstant (numeric), 8 - matrix accessor, 9 - MicroWatershedModel, 10 - MicroWatershedNetwork
        # add relevant component equations and broadcasts etc.
    
    def components(self):
        # Qin
        # Qout 
        # Vout 
        # Storage 
        # Send to Parent (trib_area_sqmi, Qtrib, wd_upstream_mgd, ps_upstream_mgd)
        # Read from Children (trib_area_sqmi, Qtrib, wd_upstream_mgd, ps_upstream_mgd)
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime

@njit
def pre_step_micro_network(op, state_ix, dict_ix):
    # this is unnecessary 
    result = False
    return result

