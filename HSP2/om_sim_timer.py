"""
The class SimTimer is used to translate copy data from one state location to another.
It is also used to make an implicit parent child link to insure that an object is loaded
during a model simulation.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from HSP2.utilities_specl import set_state
from pandas import DataFrame, DatetimeIndex
from numba import njit

class SimTimer(ModelObject):
    def __init__(self, name, container, siminfo):
        super(SimTimer, self).__init__(name, container)
        self.state_path = 'timestamp'
        self.time_array = self.dti_to_time_array(siminfo) # creates numpy formatted array of year, mo, day, ... for each timestep
        self.date_path_ix = [] # where are the are components stored in the state_ix Dict
        self.optype = 5 # 0 - ModelObject, 1 - Equation, 2 - datamatrix, 3 - ModelLinkage, 4 - BroadcastChannel, 5 - SimTimer 
    
    def register_path(self):
        # initialize the path variable if not already set
        self.ix = set_state(self.state_ix, self.state_paths, self.state_path, self.time_array[0][0])
        # now register all other paths.
        # register "year", "month" "day", ...
        year_ix = set_state(self.state_ix, self.state_paths, "/STATE/year", self.time_array[0][1])
        month_ix = set_state(self.state_ix, self.state_paths, "/STATE/month", self.time_array[0][2])
        day_ix = set_state(self.state_ix, self.state_paths, "/STATE/day", self.time_array[0][3])
        hr_ix = set_state(self.state_ix, self.state_paths, "/STATE/hour", self.time_array[0][4])
        min_ix = set_state(self.state_ix, self.state_paths, "/STATE/minute", self.time_array[0][5])
        sec_ix = set_state(self.state_ix, self.state_paths, "/STATE/second", self.time_array[0][6])
        wd_ix = set_state(self.state_ix, self.state_paths, "/STATE/weekday", self.time_array[0][7])
        dt_ix = set_state(self.state_ix, self.state_paths, "/STATE/dt", self.time_array[0][8])
        jd_ix = set_state(self.state_ix, self.state_paths, "/STATE/jday", self.time_array[0][9])
        self.date_path_ix = [year_ix, month_ix, day_ix, hr_ix, min_ix, sec_ix, wd_ix, dt_ix, jd_ix]
        self.dict_ix[self.ix] = self.time_array
        
        return self.ix
    
    def tokenize(self):
        # call parent method which sets standard ops 
        super().tokenize()
        # returns an array of data pointers
        self.ops = self.ops + [self.date_path_ix[0], self.date_path_ix[1], self.date_path_ix[2], self.date_path_ix[3], self.date_path_ix[4], self.date_path_ix[5], self.date_path_ix[6], self.date_path_ix[7], self.date_path_ix[8]]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        #self.op_tokens[self.ix] = self.ops
        super().add_op_tokens()
        self.dict_ix[self.ix] = self.time_array
    
    def dti_to_time_array(self, siminfo):
        dateindex = siminfo['tindex']
        dt = siminfo['delt']
        # sim timer is special, one entry for each time component for each timestep
        # convert DateIndex to numbers [int(i) for i in dateindex.year]
        tdi = { 0: dateindex.astype(np.int64), 1:[float(i) for i in dateindex.year], 2:[float(i) for i in dateindex.month], 3:[float(i) for i in dateindex.day], 4:[float(i) for i in dateindex.hour], 5:[float(i) for i in dateindex.minute], 6:[float(i) for i in dateindex.second], 7:[float(i) for i in dateindex.weekday], 8:[float(dt) for i in dateindex], 9:[float(i) for i in dateindex.day_of_year] }
        #tdi = { 0:dateindex.year, 1:dateindex.month, 2:dateindex.day, 3:dateindex.hour, 4:dateindex.minute, 5:dateindex.second }
        tid = DataFrame(tdi)
        time_array = tid.to_numpy()
        return time_array

# Function for use during model simulations of tokenized objects
@njit
def step_sim_timer(op_token, state_ix, dict_ix, ts_ix, step):
    # note: the op_token and state index are off by 1 since the dict_ix does not store type 
    state_ix[op_token[1]] = dict_ix[op_token[1]][step][0] # unix timestamp here 
    state_ix[op_token[2]] = dict_ix[op_token[1]][step][1] # year  
    state_ix[op_token[3]] = dict_ix[op_token[1]][step][2] # month  
    state_ix[op_token[4]] = dict_ix[op_token[1]][step][3] # day  
    state_ix[op_token[5]] = dict_ix[op_token[1]][step][4] # hour  
    state_ix[op_token[6]] = dict_ix[op_token[1]][step][5] # minute  
    state_ix[op_token[7]] = dict_ix[op_token[1]][step][6] # second 
    state_ix[op_token[8]] = dict_ix[op_token[1]][step][7] # weekday 
    state_ix[op_token[9]] = dict_ix[op_token[1]][step][8] # dt  
    state_ix[op_token[10]] = dict_ix[op_token[1]][step][9] # julian day  
    return

