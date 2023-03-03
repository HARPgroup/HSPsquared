"""
The class Broadcast is used to send and receive data to shared accumulator "channel" and "register".
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.om_model_object import ModelObject
from HSP2.om_model_linkage import ModelLinkage
from HSP2.utilities_specl import *
from numba import njit
class ModelBroadcast(ModelObject):
    def __init__(self, name, container = False, broadcast_type = 'read', broadcast_channel = False, broadcast_hub = 'self', broadcast_params = []):
        super(ModelBroadcast, self).__init__(name, container)
        # broadcast_params = [ [local_name1, remote_name1], [local_name2, remote_name2], ...]
        # broadcast_channel = state_path/[broadcast_channel]
        # broadcast_hub = self, parent, /state/path/to/element/ 
        self.linkages = {} # store of objects created by this  
        self.broadcast_type = broadcast_type
        self.optype = 4 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
        self.bc_type_id = 2 # assume read -- is this redundant?  is it really the input type ix?
        self.setup_broadcast(broadcast_type, broadcast_params, broadcast_channel, broadcast_hub)
    
    def setup_broadcast(self, broadcast_type, broadcast_params, broadcast_channel, broadcast_hub):
        if ( (broadcast_hub == 'self') or (broadcast_hub == 'child') ):
            hub_path = self.container.state_path # the parent of this object is the "self" in question
        elif broadcast_hub == 'parent':
            if (self.container.container == False):
                raise Exception("This object", container.name, "does not have a parent container. Broadcast creation halted. ")
                return False
            hub_path = self.container.container.state_path
        else:
            # we assume this is a valid path.  but we verify and fail if it doesn't work during tokenization
            hub_path = broadcast_hub
        # add thechannel to the hub path
        hub_path = hub_path + "/" + broadcast_channel
        # now iterate through pairs of source/destination broadcast lines
        i = 0
        for b_pair in broadcast_params:
            # create an object for each element in the array 
            if (broadcast_type == 'read'):
                src_path = hub_path + "/" + b_pair[1]
                # create a link object of type 2, property reader to local state 
                print("Adding broadcast read as input from ", src_path, " as local var named ",b_pair[0])
                self.bc_type_id = 2
                # create a hub if it does not exist already 
                # this will insure that there is a place for the data, and a place to 
                # add inputs for the actual broadcast items. 
                print("Creating broadcast hub ", broadcast_channel, " on ",self.container.name)
                self.linkages[i] = ModelConstant(broadcast_channel, self.container, 0.0, hub_path)
                i+=1
                # create a constant as a placeholder for the data at the hub path 
                # in case there are no senders
                print("Creating a place-holder for data for hub ", self.linkages[i-1], " var name ",b_pair[0])
                self.linkages[i] = ModelConstant(b_pair[0], self.linkages[i-1], 0.0, src_path)
                # create an input to the parent container for this variable looking at the hub path 
                self.container.add_input(b_pair[0], src_path, 1, True)
            else:
                dest_path = hub_path + "/" + b_pair[1]
                print("Adding send from local var ", b_pair[0], " to ",dest_path)
                self.bc_type_id = 4
                src_path = self.find_var_path(b_pair[0])
                self.linkages[i] = ModelLinkage(b_pair[0], self, src_path, self.bc_type_id, dest_path)
            i+=1
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        # because we added each type as a ModelLinkage, this may be superfluous?
        # this ModelLinkage will be handled on it's own.
        # are there exec hierarchy challenges because of skipping this?
        # exec hierarchy function on object.inputs[] alone.  Since broadcasts
        # are not treated as inputs, or are they? Do ModelLinkages create inputs?
        #  - should read inputs create linkages, but send/push linkages not?
        #    - ex: a facility controls a reservoir release with a push linkage 
        #          the reservoir *should* execute after the facility in this case
        #          but perhaps that just means we *shouldn't* use a push, instead 
        #          we should have the reservoir pull the info?
        #  - however, since "parent" pushes will automatically have hierarchy 
        #    preserved, since the child object already is an input to the parent 
        #    and therefore will execute before the parent
        #  - but, we must insure that ModelLinkages get executed when their container 
        #    is executed (which should come de facto as they are inputs to their container)
        #if (self.broadcast_type == 'send'):
        #    for i in self.linkages.keys():
        #        self.ops = self.ops + [self.left_ix, cop_codes[self.cop], self.right_ix]
        #else:
            # this is a read, so we simply rewrite as a model linkage 
            # not yet complete or functioning
            # self.linkage.tokenize()
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()


# njit functions for runtime
@njit
def pre_step_broadcast(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Need to iterate through the destinations (left side) and set to zero 
    # at the beginning of each timestep.
    # Not completed.
