"""
The class Broadcast is used to send and receive data to shared accumulator "channel" and "register".
See also Branch: an actual flow control structure that looks similar to Conditional, but changes execution
"""
from HSP2.state import *
from HSP2.om import *
from HSP2.om_model_object import *
from HSP2.om_model_linkage import ModelLinkage
from numba import njit
import warnings

class ModelBroadcast(ModelObject):
    def __init__(self, name, container = False, broadcast_type = 'read', broadcast_channel = False, broadcast_hub = 'self', broadcast_params = []):
        super(ModelBroadcast, self).__init__(name, container)
        self.model_props_parsed['broadcast_params'] = broadcast_params
        # broadcast_params = [ [local_name1, remote_name1], [local_name2, remote_name2], ...]
        # broadcast_channel = state_path/[broadcast_channel]
        # broadcast_hub = self, parent, /state/path/to/element/ 
        # we call handle+=_prop() because this will be OK with any format of caller data
        self.linkages = {} # store of objects created by this  
        self.optype = 4 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
        self.bc_type_id = 2 # assume read -- is this redundant?  is it really the input type ix?
        self.setup_broadcast(self.broadcast_type, self.broadcast_params, self.broadcast_channel, self.broadcast_hub)
    
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        self.broadcast_type = self.handle_prop(model_props, 'broadcast_type')
        self.broadcast_hub = self.handle_prop(model_props, 'broadcast_hub')
        self.broadcast_channel = self.handle_prop(model_props, 'broadcast_channel')
        self.broadcast_params = self.handle_prop(model_props, 'broadcast_params')
        if self.broadcast_type == None:
            self.broadcast_type = 'read'
        if self.broadcast_channel == None:
            self.broadcast_channel = False
        if self.broadcast_hub == None:
            self.broadcast_hub = 'self'
        if self.broadcast_params == None:
            self.broadcast_params = []
            
        
    
    def setup_broadcast(self, broadcast_type, broadcast_params, broadcast_channel, broadcast_hub):
        if (broadcast_hub == 'parent') and (self.container.container == False):
            warnings.warn("Broadcast named " + self.name + " is parent object " + self.container.name + " with path " + self.container.state_path + " does not have a grand-parent container. Broadcast to hub 'parent' guessing as a path-type global. ")
            broadcast_hub = '/STATE/global'
            warnings.warn("Proceeding with broadcast_type, broadcast_params, broadcast_channel, broadcast_hub = " + str(broadcast_type) + "," + str(broadcast_params) + "," + str(broadcast_channel) + "," + str(broadcast_hub))
        if ( (broadcast_hub == 'self') or (broadcast_hub == 'child') ):
            hub_path = self.container.state_path # the parent of this object is the "self" in question
            hub_container = self.container 
        elif broadcast_hub == 'parent':
            hub_path = self.container.container.state_path
            hub_container = self.container.container
        else:
            # we assume this is a valid path.  but we verify and fail if it doesn't work during tokenization
            # this is not really yet operational since it would be a global broadcast of sorts
            print("Broadcast ", self.name, " hub Path not parent, self or child.  Trying to find another hub_path = ", broadcast_hub)
            hub_path = broadcast_hub
            hub_exists = self.find_var_path(hub_path)
            if hub_exists == False:
                hub_container = False
            else:
                hub_container = self.model_object_cache[hub_path]
        # add the channel to the hub path
        channel_path = hub_path + "/" + broadcast_channel
        channel = self.insure_channel(broadcast_channel, hub_container)
        # now iterate through pairs of source/destination broadcast lines
        i = 0
        for b_pair in broadcast_params:
            # create an object for each element in the array 
            if (broadcast_type == 'read'):
                # a broadcast channel (object has been created above) 
                # + a register to hold the data (if not yet created) 
                # + an input on the parent to read the data 
                src_path = hub_path + "/" + b_pair[1]
                self.bc_type_id = 2 # pull type 
                register_varname = b_pair[0]
                # create a link object of type 2, property reader to local state 
                print("Adding broadcast read as input from ", channel_path, " as local var named ",register_varname)
                # create a register if it does not exist already 
                var_register = self.insure_register(register_varname, 0.0, channel)
                # add input to parent container for this variable from the hub path 
                self.container.add_input(register_varname, var_register.state_path, 1, True)
            else:
                # a broadcast hub (if not yet created) 
                # + a register to hold the data (if not yet created) 
                # + an input on the broadcast hub to read the data (or a push on this object?) 
                dest_path = hub_path + "/" + b_pair[1]
                self.bc_type_id = 4 # push accumulator type
                local_varname = b_pair[0] # this is where we take the data from 
                register_varname = b_pair[1] # this is the name that will be stored on the register
                print("Adding send from local var ", local_varname, " to ",channel.name)
                # create a register as a placeholder for the data at the hub path 
                # in case there are no readers
                var_register = self.insure_register(register_varname, 0.0, channel)
                dest_path = var_register.state_path
                src_path = self.find_var_path(local_varname)
                # this linkage pushes from local value to the remote path 
                pusher = ModelLinkage(register_varname, self, src_path, self.bc_type_id, dest_path)
                # try adding the linkage an input, just to see if it influences the ordering
                print("Adding broadcast source ", local_varname, " as input to register ",var_register.name)
                # we do an object connection here, as this is a foolproof way to 
                # add already created objects as inputs
                var_register.add_object_input(register_varname + str(pusher.ix), pusher, 1)
                # this linkage creates a pull on the remote path, not yet ready since 
                # there is no bc_type_id that corresponds to an accumulator pull                 
                #puller = ModelLinkage(register_varname, var_register, src_path, self.bc_type_id)
    
    def insure_channel(self, broadcast_channel, hub_container):
        print("Looking for channel ", broadcast_channel, " on ", hub_container.name)
        # must create absolute path, otherwise, it will seek upstream and get the parent 
        # we send with local_only = True so it won't go upstream 
        channel_path = hub_container.find_var_path(broadcast_channel, True)
        if channel_path == False:
            print("Creating broadcast hub ", broadcast_channel, " on ",hub_container.name)
            hub_object = ModelConstant(broadcast_channel, hub_container, 0.0)
        else:
            hub_object = self.model_object_cache[channel_path]
        return hub_object
    
    def insure_register(self, var_name, default_value, register_container):
        # we send with local_only = True so it won't go upstream 
        register_path = register_container.find_var_path(var_name, True)
        if register_path == False:
            # create a register as a placeholder for the data at the hub path 
            # in case there are no senders
            print("Creating a register for data for hub ", register_container.name, "(", register_container.state_path, ")", " var name ",var_name)
            var_register = ModelRegister(var_name, register_container, default_value)
        else:
            var_register = self.model_object_cache[register_path]
        return var_register
    
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


"""
The class ModelRegister is for storing push values.
Behavior is to zero each timestep.  This could be amended later.
Maybe combined with stack behavior?  Or accumulator?
"""
class ModelRegister(ModelConstant):
    def __init__(self, name, container = False, value = 0.0, state_path = False):
        super(ModelRegister, self).__init__(name, container, value, state_path)
        self.optype = 11 # 
        # self.state_ix[self.ix] = self.default_value
    
    def required_properties():
        req_props = super(ModelConstant, ModelConstant).required_properties()
        req_props.extend(['value'])
        return req_props

# njit functions for runtime
@njit
def pre_step_register(op, state_ix, dict_ix):
    ix = op[1]
    #print("Resetting register", ix,"to zero")
    state_ix[ix] = 0.0

@njit
def pre_step_broadcast(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Need to iterate through the destinations (left side) and set to zero 
    # at the beginning of each timestep.
    # Not completed.
