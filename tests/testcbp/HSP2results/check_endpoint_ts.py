# Must be run from the HSPsquared source directory, the h5 file has already been setup with hsp import_uci test10.uci
# bare bones tester - must be run from the HSPsquared source directory
import os
from HSP2.main import *
from HSP2.om import *
import HSP2IO
import numpy
from HSP2IO.hdf import HDF5
from HSP2IO.io import IOManager
fpath = './tests/test10/HSP2results/test10.h5' 
# try also:
# fpath = './tests/testcbp/HSP2results/PL3_5250_0001.h5' 
# sometimes when testing you may need to close the file, so try:
# f = h5py.File(fpath,'a') # use mode 'a' which allows read, write, modify
# # f.close()
hdf5_instance = HDF5(fpath)
io_manager = IOManager(hdf5_instance)
uci_obj = io_manager.read_uci()
siminfo = uci_obj.siminfo
opseq = uci_obj.opseq
# Note: now that the UCI is read in and hdf5 loaded, you can see things like:
# - hdf5_instance._store.keys() - all the paths in the UCI/hdf5
# - finally stash specactions in state, not domain (segment) dependent so do it once
# now load state and the special actions
state = init_state_dicts()
state_initialize_om(state)
state['specactions'] = uci_obj.specactions # stash the specaction dict in state

state_siminfo_hsp2(uci_obj, siminfo)
# Add support for dynamic functions to operate on STATE
# - Load any dynamic components if present, and store variables on objects 
state_load_dynamics_hsp2(state, io_manager, siminfo)
# Iterate through all segments and add crucial paths to state 
# before loading dynamic components that may reference them
state_init_hsp2(state, opseq, activities)
state_load_dynamics_specl(state, io_manager, siminfo) # traditional special actions
state_load_dynamics_om(state, io_manager, siminfo) # operational model for custom python
state_om_model_run_prep(state, io_manager, siminfo) # this creates all objects from the UCI and previous loads
# state['model_root_object'].find_var_path('RCHRES_R001')
# Get the timeseries naked, without an object
rchres1 = state['model_object_cache']['/STATE/RCHRES_R001']
precip_ts = ModelLinkage('precip_in', rchres1, {'right_path':'/TIMESERIES/TS039', 'link_type':3})
# write it back.  We can give an arbitrary name or it will default to write back to the source path in right_path variable
ts1 = precip_ts.read_ts() # same as precip_ts.ts_ix[precip_ts.ix], same as state['ts_ix'][precip_ts.ix]
# we can specify a custom path to write this TS to
precip_ts.write_path = '/RESULTS/test_TS039'
precip_ts.write_ts()
# precip_ts.write_ts is same as:
#     ts4 = precip_ts.format_ts(ts1, ['tsvalue'], siminfo['tindex'])
#     ts4.to_hdf(precip_ts.io_manager._output._store, precip_ts.write_path, format='t', data_columns=True, complevel=precip_ts.complevel)

tsdf = pd.DataFrame(data=ts1, index=siminfo['tindex'],columns=None)
# verify 
ts1 = precip_ts.read_ts() # same as precip_ts.ts_ix[precip_ts.ix], same as state['ts_ix'][precip_ts.ix]
# should yield equivalent of:
ts2 = hdf5_instance._store[precip_ts.ts_path]
# data_frame.to_hdf(self._store, path, format='t', data_columns=True, complevel=complevel)
ts3 = hdf5_instance._store[precip_ts.write_path]
# and is same as
ts4 = precip_ts.io_manager._output._store[precip_ts.write_path]
