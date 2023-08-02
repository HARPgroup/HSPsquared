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

class SimpleChannel(ModelObject):
    def __init__(self, name, container = False, model_props = []):
        super(SimpleChannel, self).__init__(name, container)
        self.model_props_parsed = model_props
        self.optype = 13 # see list in om_model_object.py
        # add basic numeric state variables for outputs
        self.rvars = {'solver', 'Qin', 'Rin', 'drainage_area', 'area', 'demand'}
        # old method had q_var, then reported it as Qin this can just be a link or constant
        # and therefore handled by constant_or_path()
        self.wvars = {'Qout', 'depth', 'its', 'Storage', 'last_S', 'rejected_demand_mgd', 'rejected_demand_pct', 'area', 'demand', 'drainage_area'}
        self.r_var_values = {}
        self.w_var_values = {}
        self.var_ops = [] # keep these separate to easily add to ops at tokenize
        self.autosetvars = True # this should default to False or True?
        self.parse_model_props(model_props)
        self.add_input('dt','dt') # must have this 
        self.set_local_props()
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        super().parse_model_props(model_props, strict)
        if model_props.get('solver') == None:
            model_props['solver'] = 0 # use simple-routing by default 
        # ceck for inputs that this will use to get flows/demand inputs 
        for op_name in self.rvars:
            self.r_var_values[op_name] = self.handle_prop(model_props, op_name, False)
        # handle variables that used a weird convention in old model
        if 'q_var' in model_props:
            self.r_var_values['Qin'] = self.handle_prop(model_props, 'q_var', False)
        if 'r_var' in model_props:
            self.r_var_values['Rin'] = self.handle_prop(model_props, 'r_var', False)
        if 'w_var' in model_props:
            self.r_var_values['demand'] = self.handle_prop(model_props, 'w_var', False)
        return True
    
    def set_local_props(self):
       # this sets up local variables.  These are with a parent path, or self path 
       # [channel name]_Qout - the outflow from this channel 
       for i in self.wvars:
           # Passing a numeric value (like 0.0) to this forces creation of ModelConstant
           self.constant_or_path(i, 0.0, True)
           if self.autosetvars == True:
               i_object = self.get_object(i)
               self.container.add_object_input(self.name + '_' + i, i_object, 1)
    
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
        order_ops = ['solver', 'dt', 'Qin', 'Rin', 'Qout', 'demand', 'Storage']
        for i in order_ops:
            self.var_ops.append(self.inputs_ix[i])
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()
        self.ops = self.ops + self.var_ops

# njit functions for runtime
@njit
def pre_step_simple_channel(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Not yet completed. Maybe we do not need any pre-step actions?

@njit
def step_simple_channel(op, state_ix, dict_ix):
    ix = op[1] # note op[0] is op type which is known if we are here.
    # Not yet completed.
    # 3 options for solver:
    #   - 0: Qout = Qin
    #   - 1: Euler
    #   - 2: 3-d surface
    #   - 3: Newton's Method
    # type = op[0], ix = op[1]
    solver = op[2]
    dt_ix = op[3]
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
    dts = (state_ix[dt_ix] * 60)
    if (solver == 0):
        Qout = Qin - wd_mgd * 1.547 / dts + ps_mgd * 1.547 / dts
    elif (solver > 0):
        # all will be simple routing until end
        Qout = Qin - wd_mgd * 1.547 / dts + ps_mgd * 1.547 / dts
    print("Calcing store_change with ix:", storage_ix)
    store_change = (Qin - Qout) * dt # change in storage in cubic feet 
    return
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
