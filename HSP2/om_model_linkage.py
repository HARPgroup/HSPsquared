"""
The class ModelLinkage is used to translate copy data from one state location to another.
It is also used to make an implicit parent child link to insure that an object is loaded
during a model simulation.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from numba import njit
class ModelLinkage(ModelObject):
    def __init__(self, name, container = False, right_path = '', link_type = 1, left_path = False):
        super(ModelLinkage, self).__init__(name, container)
        # ModelLinkage copies a values from right to left
        # right_path: is the data source for the link 
        # left_path: is the destination of the link 
        # left_path: is implicit in types 1-3, i.e., the ModelLinkage object path itself is the left_path 
        #   - left_path parameter is only needed for pushes (type 4 and 5)
        #   - the push is functionally equivalent to a pull whose path resolves to the specified left_path  
        #   - but the push allows the potential for multiple objects to set a single state 
        #     This can be dangerous or difficult to debug, but essential to replicate old HSPF behaviour
        #     especially in the case of If/Then type structures.
        #     it is also useful for the broadcast objects, see om_model_broadcast for those 
        # link_type: 1 - local parent-child, 2 - local property link (state data), 3 - remote linkage (ts data only), 4 - push to accumulator (like a hub), 5 - overwrite remote value 
        self.optype = 3 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - ModelLinkage, 4 - 
        if container == False:
            # this is required
            print("Error: a link must have a container object to serve as the destination")
            return False
        if left_path == False:
            # self.state_path gets set when creating at the parent level
            left_path = self.state_path 
        self.right_path = right_path
        self.left_path = left_path 
        self.link_type = link_type 
        # this breaks for some reason, doesn't like the input name being different than the variable path ending?        
        self.add_input(self.right_path, self.right_path)
    
    def find_paths(self):
        # this should be needed if this is a PUSH link_type = 4 or 5
        super().find_paths()
        self.paths_found = False # override parent setting until we verify everything
        # do we need to do this, or just trust it exists?
        #self.insure_path(self, self.right_path)
        # the left path, if this is type 4 or 5, is a push, so we must require it 
        if ( (self.link_type == 4) or (self.link_type == 5) ):
            self.insure_path(self.left_path)
        self.paths_found = True
        return 
        
    def tokenize(self):
        super().tokenize()
        # - if this is a data property link then we add op codes to do a copy of data from one state address to another 
        # - if this is simply a parent-child connection, we do not render op-codes, but we do use this for assigning
        # - execution hierarchy
        if self.link_type in (2, 3):
            src_ix = get_state_ix(self.state_ix, self.state_paths, self.right_path)
            if not (src_ix == False):
                self.ops = self.ops + [src_ix, self.link_type]
            else:
                print("Error: link ", self.name, "does not have a valid source path")
            #print("tokenize() result", self.ops)
        if (self.link_type == 4) or (self.link_type == 5):
            # we push to the remote path in this one 
            left_ix = get_state_ix(self.state_ix, self.state_paths, self.left_path)
            right_ix = get_state_ix(self.state_ix, self.state_paths, self.right_path)
            if (left_ix != False) and (right_ix != False):
                self.ops = self.ops + [left_ix, self.link_type, right_ix]
            else:
                print("Error: link ", self.name, "does not have valid paths", "(left = ", self.left_path, left_ix, "right = ", self.right_path, right_ix, ")")
            #print("tokenize() result", self.ops)

# Function for use during model simulations of tokenized objects
@njit
def step_model_link(op_token, state_ix, ts_ix, step):
    if step == 2:
        print("step_model_link() called at step 2 with op_token=", op_token)
    if op_token[3] == 1:
        return True
    elif op_token[3] == 2:
        state_ix[op_token[1]] = state_ix[op_token[2]]
    elif op_token[3] == 3:
        # read from ts variable TBD
        # state_ix[op_token[1]] = ts_ix[op_token[2]][step]
        return True
    elif op_token[3] == 4:
        # add value in local state to the remote broadcast hub+register state 
        state_ix[op_token[2]] = state_ix[op_token[2]] + state_ix[op_token[4]]
        return True
    elif op_token[3] == 5:
        # overwrite remote variable state with value in another paths state
        if step == 2:
            print("Setting state_ix[", op_token[2], "] =", state_ix[op_token[4]])
        state_ix[op_token[2]] = state_ix[op_token[4]]
        return True


def test_model_link(op_token, state_ix, ts_ix, step):
    if op_token[3] == 1:
        return True
    elif op_token[3] == 2:
        state_ix[op_token[1]] = state_ix[op_token[2]]
    elif op_token[3] == 3:
        # read from ts variable TBD
        # state_ix[op_token[1]] = ts_ix[op_token[2]][step]
        return True
    elif op_token[3] == 4:
        print("Remote Broadcast accumulator type link.")
        print("Setting op ID", str(op_token[2]), "to value from ID", str(op_token[4]), "with value of ")
        # add value in local state to the remote broadcast hub+register state 
        state_ix[op_token[2]] = state_ix[op_token[2]] + state_ix[op_token[4]]
        print(str(state_ix[op_token[2]]) + " = ", str(state_ix[op_token[2]]) + "+" + str(state_ix[op_token[4]]))
        return True
    elif op_token[3] == 5:
        # push value in local state to the remote broadcast hub+register state 
        state_ix[op_token[2]] = state_ix[op_token[4]]
        return True