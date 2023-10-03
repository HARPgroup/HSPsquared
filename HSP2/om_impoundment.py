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

class SimpleImpoundment(ModelObject):
    def __init__(self, name, container = False, model_props = []):
        super(SimpleImpoundment, self).__init__(name, container)
        self.model_props_parsed = model_props
        self.optype = 14 # see list in om_model_object.py
        # add basic numeric state variables for outputs
        self.rvars = array{'et_in','precip_in','release','demand', 'Qin', 'refill', 'max_capacity'};
        #since this is a subcomp need to explicitly declare which write on parent
        self.wvars = array{'Qin', 'evap_mgd', 'precip_mgd','Qout','lake_elev','Storage', 'refill_full_mgd', 'demand', 'use_remain_mg', 'days_remaining', 'max_usable', 'riser_stage', 'riser_head', 'riser_mode', 'riser_flow', 'riser_diameter', 'demand_met_mgd', 'its', 'spill', 'release', 'area', 'refill', 'precip_mgd', 'evap_mgd');
        self.r_var_values = {}
        self.w_var_values = {}
        self.var_ops = [] # keep these separate to easily add to ops at tokenize
        self.autosetvars = True # this should default to False or True?
        self.parse_model_props(model_props)
        self.add_input('dts','dts') # must have this 
        self.set_local_props()
    
    def parse_model_props(self, model_props, strict = False ):
        # handle props array 
        super().parse_model_props(model_props, strict)
        # set up the read variables, this retrieves whatever was passed in
        # later, in find_paths() we will determine if these inputs are constants or variables
        for op_name in self.rvars:
            self.r_var_values[op_name] = self.handle_prop(model_props, op_name, False)
        if model_props.get('solver') == None:
            model_props['solver'] = 0 # use simple-routing by default 
        # see SimpleChannel for this use 
        return True
    
    def set_local_props(self):
       # this sets up local variables.  These are with a parent path, or self path 
       # [channel name]_Qout - the outflow from this channel 
       for i in self.wvars:
           # We use constant_or_path() here because the children comps HAVE to be present
           # Can we do the same for ivars? We do NOT, instead doing them at find_paths()
           # in a method similar to Equation
           # Passing a numeric value (like 0.0) to this forces creation of ModelConstant
           self.constant_or_path(i, 0.0, True)
           if self.autosetvars == True:
               i_object = self.get_object(i)
               self.container.add_object_input(self.name + '_' + i, i_object, 1)
    
    def find_paths(self):
        super().find_paths()
        self.paths_found = False # override parent setting until we verify everything
        # handle props array 
        for op_name in self.r_var_values:
            self.constant_or_path(op_name, self.r_var_values[op_name], False)
        # the above should result in all rvars as inputs, whether constant or variables
        # then, when we tokenize, we just refer to self.inputs['var_name'] to get the ix 
        self.paths_found = True
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        op_num = 0
        # todo: add riser structure parameters
        # format these in such a way that it makes it easy to keep the numbers
        # straight down in the njit code
        order_ops = [
            'solver', 'dts', 
            'Qin', 'refill', 'Qout', 
            'demand', 'release', 'Storage', 'discharge', 
            'et_in', 'precip', 
            'max_capacity', 'use_remain_mg', 'area',
            'unusable_storage', 'lake_elev', 'storage_mg'
        ]
        for i in order_ops:
            self.var_ops.append(self.inputs_ix[i])
        self.ops = self.ops + self.var_ops
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime
@njit
def pre_step_impoundment(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # Not yet completed. Needed?

@njit
def om_impoundment_simple_hydro(op, state_ix, dict_ix):
    """
    Calculate flows and water balance and water levels with simple Qout = Storage - max_capacity
    """
    # data state indices for given vars:
    ix, solver, dts_ix = op[1], op[2], op[3]
    Qin_ix, refill_ix, Qout_ix = op[4], op[5], op[6]
    demand_ix, release_ix, storage_ix, discharge_ix = op[7], op[8], op[9], op[10] 
    et_ix, precip_ix = op[11], op[12] 
    Smax_ix, use_remain_mg_ix, area_ix = op[13], op[14], op[15] 
    unusable_storage_ix, lake_elev_ix, storage_mg_ix = op[16], op[17], op[18]
    
    S0 = state_ix[storage_ix]; # storage at end of previous timestep (ac-ft)
    Qin = state_ix[Qin_ix];
    demand = state_ix[demand_ix]; # assumed to be in MGD
    refill = state_ix[refill_ix]; # assumed to be in MGD
    discharge = state_ix[discharge_ix]; # assumed to be in MGD
    release = state_ix[release_ix]; 
    pan_evap = state_ix[et_ix];
    precip = state_ix[precip_ix];
    dts = state_ix[dts_ix] # simulation timestep in seconds
    max_capacity = state_ix[Smax_ix];
    area = state_ix[area_ix]
    unusable_storage = state_ix[unusable_storage_ix]
    
    # calculations
    evap_acfts = area * pan_evap / 12.0 / 86400.0;
    precip_acfts = area * precip / 12.0 / 86400.0; 

    storechange = S0 + ((Qin - release) * dts / 43560.0) + (1.547 * discharge * dts / 43560.0)  + (1.547 * refill * dts / 43560.0) - (1.547 * demand * dts /  43560.0) - (evap_acfts * dts) + (precip_acfts * dts);
    if (storechange < 0) {
        # what to do with flowby & wd?
        # if storechange is less than zero, its magnitude represents the deficit of flowby+demand
        # we can either choose to evenly distribute them or assume that demand wins
        deficit_acft = abs(storechange);
        s_avail = (1.547 * demand * dts /  43560.0) + (release * dts /  43560.0) - deficit_acft;
        if (s_avail <= (1.547 * demand * dts /  43560.0)) {
            # no water available for flowby
            release = 0.0;
            demand_met_mgd = s_avail * 43560.0 / (1.547 * dts);
        } else {
            # flowby is remainder
            release = (s_avail - (1.547 * demand * dts /  43560.0)) * 43560.0 / dts;
            demand_met_mgd = demand;
        }
        storechange = 0;
    } else {
        demand_met_mgd = demand;
        deficit_acft = 0.0;
    }
    Storage = min([storechange, max_capacity]);
    if (storechange > max_capacity) {
        spill = (storechange - max_capacity) * 43560.0 / dts;
    } else {
        spill = 0;
    }
    if (Storage < 0.0) {
        Storage = 0.0;
    }
    Qout = spill + release;
    lake_elev = 0.0 # tbd
    state_ix[use_remain_mg_ix] = (Storage - unusable_storage) / 3.07;
    state_ix[storage_ix] = Storage;
    state_ix[Qout_ix] = Qout;
    state_ix[lake_elev_ix] = lake_elev;
    state_ix[storage_mg_ix] = Storage / 3.07;
    '''
    # set all states, include local unit conversion dealios
    state_ix['evap_mgd'] = evap_acfts * 28157.7;
    state_ix['precip_mgd'] = precip_acfts * 28157.7;
    state_ix['pct_use_remain'] = (Storage - unusable_storage) / (max_capacity - unusable_storage);
    if (state_ix['use_remain_mg'] < 0) {
       state_ix['use_remain_mg'] = 0;
       state_ix['pct_use_remain'] = 0;
    }
    # days remaining
    if ( ($demand > 0) and (dts > 0)) {
       $days_remaining = state_ix['use_remain_mg'] / ($demand);
    } else {
       $days_remaining = 0;
    }
    state_ix['days_remaining'] = $days_remaining;
    state_ix['deficit_acft'] = $deficit_acft;
    state_ix['demand_met_mgd'] = $demand_met_mgd;
    state_ix['depth'] = $stage;
    state_ix['Vout'] = $Vout;
    state_ix['Storage'] = $Storage;
    state_ix['spill'] = $spill;
    state_ix['release'] = $release;
    state_ix['area'] = $area;
    state_ix['evap_acfts'] = $evap_acfts;
    state_ix['refill_full_mgd'] = (($max_capacity - $Storage) / 3.07) * (86400.0 / dts);
    '''
    return


@njit
def om_impoundment_riser_hydro(op, state_ix, dict_ix):
    """
    Calculate flows and water balance and water levels with Qout = f(Storage, riser dims)
    Not yet completed. Just return simple.
    """
    om_impoundment_simple_hydro(op, state_ix, dict_ix)

@njit
def step_impoundment(op, state_ix, dict_ix, step):
    ix = op[1] # note op[0] is op type which is known if we are here.
    # Not yet completed.
    # 3 options for solver:
    #   - 0: simple overflow max storage with release 
    #   - 1: riser structure with release 
    # type = op[0], ix = op[1]
    solver = op[2]
    if solver == 0:
        om_impoundment_simple_hydro(op, state_ix, dict_ix)
    else:
        om_impoundment_simple_hydro(op, state_ix, dict_ix)
    return
