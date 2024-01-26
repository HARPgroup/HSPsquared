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

class Impoundment(ModelObject):
    def __init__(self, name, container = False, model_props = []):
        # add basic numeric state variables for outputs
        print("Createing Impoundment named", name)
        self.rvars = {'et_in','precip_in','release','demand', 'Qin', 'refill'}
        self.r_var_values = {}
        # since this is a subcomp need to explicitly declare which write on parent
        self.wvars = {'Qin', 'evap_mgd', 'precip_mgd','Qout','lake_elev','Storage', 'refill_full_mgd', 'demand', 'use_remain_mg', 'pct_use_remain', 'days_remaining', 'max_usable', 'riser_stage', 'riser_head', 'riser_mode', 'riser_flow', 'riser_diameter', 'demand_met_mgd', 'its', 'spill', 'release', 'area', 'refill'}
        self.w_var_ix = {} # where to store indices for writign vars
        # by calling the parent without model_props
        super(Impoundment, self).__init__(name, container, model_props)
        self.optype = 13 # see list in om_model_object.py
        self.var_ops = [] # keep these separate to easily add to ops at tokenize
        self.autosetvars = True # this should default to False or True?
        self.add_input('dts','dts') # must have this 
        self.set_local_props()
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        super().parse_model_props(model_props, strict)
        print("parse_model_props() Looking for ", self.rvars)
        for op_name in self.rvars:
            op_in = self.handle_prop(model_props, op_name, False, 0.0)
            oix = self.constant_or_path(op_name, op_in, True)
            print("Added reader for", op_name, "with index", oix)
            # creates a copy on the parent like local_channel_Qin etc
        return True
    
    def set_local_props(self):
        # this sets up local variables.  These are with a parent path, or self path 
        # these vars may come in as inputs, or be intermediate outputs.
        # regardless, the purpose of this is to create a variable on the parent
        # that appends the variable to the name of this object
        # example name = impoundment
        #   Qout: create:
        #     impoundment/Qout + link to [parent]/impoundment_Qout
        #   and the parent variable is just a copy
        #   Qin:
        #     impoundment/Qin + [parent]/impoundment_Qin
        #   and the parent variable is just a copy
        # [channel name]_Qout - the outflow from this channel 
        for i in self.wvars:
            if i in self.inputs:
                right_path = self.inputs[i]
            else:
                # Create a numeric slot by passing 0.0 (or any numeric value) to constant_or_path()
                default_value = 0.0
                var_register = ModelRegister(i, self, default_value)
                right_path = var_register.state_path
            # store iix somewhere for tokenizing
            if (self.autosetvars == True):
                parent_var_name = str(self.name) + "_" + str(i)
                self.create_parent_var(parent_var_name, right_path)
    
    def find_paths(self):
        super().find_paths()
        # todo:
        #   - r_var, q_var, etc are inputs, that link to a remote variables
        #   - their local state counterparts such as Qin, Rin, etc 
        #     MUST be distinct entities, since they are recorded in STATE
        #   - This, local state counterparts (all wvars and anything else we want to store)
        #     must be created as ModelConstant with an appropriate path 
        #   - When tokenizing, we need to store both source and local-state IDs for 
        #     getting and setting 
        #   NOTE: the below setting of constant_or_path for these local-state variables 
        #         will be un-neccessary, since we will need to create constants earlier
        #         in the model parsing process.
        self.paths_found = False # override parent setting until we verify everything
        # handle props array 
        for op_name in self.r_var_values:
            self.constant_or_path(op_name, self.r_var_values[op_name], False)
        # the above should result in all rvars as inputs, whether constant or variables
        # then, when we tokenize, we just refer to self.inputs['q_var'] to get the ix 
        self.paths_found = True
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        op_num = 0
        order_ops = ['solver', 'dts', 'Qin', 'Rin', 'Qout', 'demand', 'Storage']
        for i in order_ops:
            self.var_ops.append(self.inputs_ix[i])
        self.ops = self.ops + self.var_ops
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime
@njit
def pre_step_simple_channel(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Not yet completed. Maybe we do not need any pre-step actions?

@njit
def step_simple_channel(op, state_ix, dict_ix, step):
    ix = op[1] # note op[0] is op type which is known if we are here.
    # Not yet completed.
    # 3 options for solver:
    #   - 0: Qout = Qin
    #   - 1: Euler
    #   - 2: 3-d surface
    #   - 3: Newton's Method
    # type = op[0], ix = op[1]
    solver = op[2]
    dts_ix = op[3]
    Qin_ix = op[4] # the data state index for the Qin variable (upstream inflow)
    Rin_ix = op[5] # the data state index for the Rin variable (local inflow)
    Qout_ix = op[6] # the data state index for the Qout variable 
    demand_ix = op[7] # the data state index for the Qout variable 
    storage_ix = op[8] # the data state index for the Qout variable 
    # solver: op[2], Qin_ix = op[3], Qout_ix: op[4], demand_ix: op[5], storage_ix: op[6]
    # discharge_ix: op[7], et_ix: op[8], precip_ix: op[9]
    # if this object uses anything other than Qout = Qin
    # get ix for: Qin,
    Qin = state_ix[Qin_ix] + state_ix[Rin_ix]
    wd_mgd = state_ix[demand_ix]
    #ps_mgd = state_ix[discharge_ix]
    ps_mgd = 0 # temp for now
    Qout = Qin
    S1 = state_ix[storage_ix] # initial storage from end of last time step 
    # Simple Routing
    dts = state_ix[dts_ix]
    if (solver == 0):
        Qout = Qin - wd_mgd * 1.547 / dts + ps_mgd * 1.547 / dts
    elif (solver > 0):
        # all will be simple routing until end
        Qout = Qin - wd_mgd * 1.547 / dts + ps_mgd * 1.547 / dts
    store_change = (Qin - Qout) * dts # change in storage in cubic feet 
    S2 = S1 + store_change
    if (S2 < 0):
        S2 = 0
        Qout = S1 / dts # exact rate needed to empty channel in 1 step.
    state_ix[Qout_ix] = Qout
    state_ix[storage_ix] = S2
    # TBD (or not depending on what is useful)
    #state_ix[V_ix] = Vout;
    #state_ix[area_ix] = area;
    #state_ix[depth_ix] = depth;
    #state_ix['last_demand'] = $demand;
    #state_ix['last_discharge'] = $discharge;
    #state_ix['rejected_demand_mgd'] = $rejected_demand_mgd;
    #state_ix['rejected_demand_pct'] = $rejected_demand_pct;
    #state_ix['its'] = $its;
    return True
