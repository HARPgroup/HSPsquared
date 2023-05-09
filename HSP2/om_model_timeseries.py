"""
The class ModelTimeseries is used to translate copy data from one state location to another.
It is also used to make an implicit parent child link to insure that an object is loaded
during a model simulation.
"""
import HSP2IO
from HSP2IO.hdf import HDF5
from HSP2IO.io import IOManager
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
import numpy as np
import time
from numba.typed import Dict
from numba import njit
class ModelTimeseries(ModelObject):
    def __init__(self, name, container = False, value = 0.0, state_path = False):
        if (state_path != False):
            # this allows us to mandate the location. useful for placeholders, broadcasts, etc.
            self.state_path = state_path
        super(ModelTimeseries, self).__init__(name, container)
        self.default_value = float(value) 
        self.optype = 11 # 11 - ModelTimeseries (numeric)
        #print("ModelTimeseries named",self.name, "with path", self.state_path,"and ix", self.ix, "value", value)
        var_ix = self.set_state(float(value))
        self.paths_found = True
        # self.state_ix[self.ix] = self.default_value
    
    # helper/loader functions for model setup
    def load_sim_ts(self, io_manager, siminfo, var_path, how_transform=False):
        # This uses hsp2 plumbing completely, another uses 
        # - need to trim path
        # - Note: this only supports things in the TIMESERIES/ path 
        ts_name = var_path.replace("/TIMESERIES/","")
        ts_name = ts_name.replace("TIMESERIES/","")
        # reads data, converts to appropriate time scale
        # read_ts(category:Category, operation:Union[str,None]=None, segment:Union[str,None]=None, activity:Union[str,None]=None)
        ts = io_manager.read_ts(Category.INPUTS, None, ts_name)
        # TODO: could support a more generic approach
        # - Load first using pandas 
        # dstore = pd.HDFStore(fpath)
        # dset = read_hdf(dstore, '/TIMESERIES/TS011/')
        # - Then, use transform method from HSP2IO/hdf.py 
        # t = transform(dset, MEMBER?, how_transform, siminfo)
        # t = transform(dset, 'NA', 'SAME', siminfo)
        # add to ts_ix
        self.ts_ix[self.ix] = np.asarray(ts, dtype="float64")

@njit
def pre_step_timeseries(state_ix, ts_ix, step):
    for idx in ts_ix.keys():
        state_ix[idx] = ts_ix[idx][step] # the timeseries inputs state get set here. 

# testing:
# ROin = ModelTimeseries('ROin', False, 0.0, '/TIMESERIES/TS010')
# ROin.load_sim_ts(io_manager, siminfo, '/TIMESERIES/TS010', False)
