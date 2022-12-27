"""
The class SimTimer is used to translate copy data from one state location to another.
It is also used to make an implicit parent child link to insure that an object is loaded
during a model simulation.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from pandas import DataFrame

from numba import njit
class SimTimer(ModelObject):
    def __init__(self, name, container, dateindex):
        super(SimTimer, self).__init__(name, container)
        self.state_path = 'timestamp'
        self.time_array = dti_to_time_array(dateindex) # creates numpy formatted array of year, mo, day, ... for each timestep
        self.date_path_ix = [] # where are the are components stored in the state_ix Dict
        self.optype = 3 # 0 - ModelObject, 1 - Equation, 2 - datamatrix, 3 - ModelLinkage, 4 - BroadcastChannel, 5 - SimTimer 
    
    def register_path(self):
        # initialize the path variable if not already set
        self.ix = set_state(self.state_ix, self.state_paths, self.state_path, self.default_value)
        # now register all other paths.
        # register "year", "month" "day", ...
        year_ix = set_state(self.state_ix, self.state_paths, "/STATE/year", self.default_value)
        month_ix = set_state(self.state_ix, self.state_paths, "/STATE/month", self.default_value)
        day_ix = set_state(self.state_ix, self.state_paths, "/STATE/day", self.default_value)
        hr_ix = set_state(self.state_ix, self.state_paths, "/STATE/hour", self.default_value)
        min_ix = set_state(self.state_ix, self.state_paths, "/STATE/minute", self.default_value)
        sec_ix = set_state(self.state_ix, self.state_paths, "/STATE/second", self.default_value)
        wd_ix = set_state(self.state_ix, self.state_paths, "/STATE/weekday", self.default_value)
        ym_ix = set_state(self.state_ix, self.state_paths, "/STATE/yearmo", self.default_value)
        jd_ix = set_state(self.state_ix, self.state_paths, "/STATE/jday", self.default_value)
        self.date_path_ix = [year_ix, month_ix, day_ix, hr_ix, min_ix, sec_ix, wd_ix, ym_ix, jd_ix]
        self.dict_ix[self.ix] = self.time_array
        
        return self.ix
    
    def tokenize(self):
        # returns an array of data pointers
        self.ops = [5, self.ix, self.date_path_ix[0], self.date_path_ix[1], self.date_path_ix[2], self.date_path_ix[3], self.date_path_ix[4], self.date_path_ix[5], self.date_path_ix[6], self.date_path_ix[7], self.date_path_ix[8]]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        #self.op_tokens[self.ix] = self.ops
        super().add_op_tokens()
        self.dict_ix[self.ix] = self.time_array


def dti_to_time_array(dateindex):
    # sim timer is special, one entry for each time component for each timestep
    # convert DateIndex to numbers [int(i) for i in dateindex.year]
    tdi = { 0:[float(i) for i in dateindex.year], 1:[float(i) for i in dateindex.month], 2:[float(i) for i in dateindex.day], 3:[float(i) for i in dateindex.hour], 4:[float(i) for i in dateindex.minute], 5:[float(i) for i in dateindex.second] }
    #tdi = { 0:dateindex.year, 1:dateindex.month, 2:dateindex.day, 3:dateindex.hour, 4:dateindex.minute, 5:dateindex.second }
    tid = DataFrame(tdi)
    time_array = tid.to_numpy()
    return time_array

# Function for use during model simulations of tokenized objects
@njit
def step_sim_timer(op_token, state_ix, dict_ix, ts_ix, step):
    state_ix[op_token[1]] = 0 # todo: put an integer unix timestamp here 
    state_ix[op_token[2]] = dict_ix[op_token[1]][step][0] # year  
    state_ix[op_token[3]] = dict_ix[op_token[1]][step][1] # month  
    return True

