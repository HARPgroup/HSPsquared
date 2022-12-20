"""
The class ModelLinkage is used to translate copy data from one state location to another.
It is also used to make an implicit parent child link to insure that an object is loaded
during a model simulation.
"""
from HSP2.om_model_object import ModelObject
from numba import njit
class ModelLinkage(ModelObject):
    def __init__(self, name, container = False, source_path = '', link_type = 1):
        super(ModelLinkage, self).__init__(name, container)
        if container == False:
            # this is required
            print("Error: a link must have a container object to serve as the destination")
            return False
        self.source_path = source_path
        self.link_type = link_type # 1 - local parent-child, 2 - local property link (state data), 3 - remote linkage (ts data only)
        self.optype = 3 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - ModelLinkage, 4 - broadcastChannel, 5 - ?
    
    def tokenize(self):
        self.ops = []
        # - if this is a data property link then we add op codes to do a copy of data from one state address to another 
        # - if this is simply a parent-child connection, we do not render op-codes, but we do use this for assigning
        # - execution hierarchy
        if self.link_type in (2, 3):
            src_ix = get_state_ix(self.state_ix, self.state_paths, self.source_path)
            if not (src_ix == False):
                self.ops = [self.optype, self.ix, src_ix, self.link_type]
            else:
                print("Error: link ", self.name, "does not have a valid source path")

# Function for use during model simulations of tokenized objects
@njit
def step_model_link(op_token, state_ix, ts_ix, step):
    if op_token[3] == 1:
        return True
    elif op_token[3] == 2:
        state_ix[op_token[1]] = state_ix[op_token[2]]
    elif op_token[3] == 3:
        return True
        # state_ix[op_token[1]] = ts_ix[op_token[2]][step]
