import os
from hsp2.hsp2.main import *
from hsp2.hsp2.om import *
from hsp2.hsp2.state import *
import numpy
from hsp2.hsp2io.hdf import HDF5
from hsp2.hsp2io.io import IOManager
# fpath = './tests/testcbp/HSP2results/JL1_6562_6560.h5'
fpath = 'C:/WorkSpace/modeling/projects/james_river/rivanna/beaver_hsp2/JL1_6562_6560.h5'

# try also:
# fpath = './tests/testcbp/HSP2results/JL1_6562_6560.h5'
# sometimes when testing you may need to close the file, so try openg and closing with h5py:
#    note: h5py: may need to pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --default-timeout=100 h5py
#  
# f = h5py.File(fpath,'a') # use mode 'a' which allows read, write, modify
# # f.close()
hdf5_instance = HDF5(fpath)


## Does this help not cut off the i in io?
io_manager = IOManager(hdf5_instance)
uci_obj = io_manager.read_uci()
siminfo = uci_obj.siminfo
opseq = uci_obj.opseq
# Note: now that the UCI is read in and hdf5 loaded, you can see things like:
# - hdf5_instance._store.keys() - all the paths in the UCI/hdf5
# - finally stash specactions in state, not domain (segment) dependent so do it once
# now load state and the special actions
state = init_state_dicts()
state_siminfo_hsp2(uci_obj, siminfo, io_manager, state)
# Iterate through all segments and add crucial paths to state
# before loading dynamic components that may reference them
state_init_hsp2(state, opseq, activities)
om_init_state(state)
state['specactions'] = uci_obj.specactions # stash the specaction dict in state

# Add support for dynamic functions to operate on STATE
# - Load any dynamic components if present, and store variables on objects
state_load_dynamics_hsp2(state, io_manager, siminfo)
specl_load_state(state, io_manager, siminfo) # traditional special actions
state_load_dynamics_om(state, io_manager, siminfo) # operational model for custom python
state_om_model_run_prep(state, io_manager, siminfo)
# Inspect the dynamic stuff
# Can use the discovery tools like so:
river = state['model_root_object'].get_object('RCHRES_R001')
wd_cfs = river.get_object('wd_cfs')
ts1 = wd_cfs.get_object('store_ts') # same as precip_ts.ts_ix[precip_ts.ix], same as state['ts_ix'][precip_ts.ix]
ts1.io_manager = io_manager
from pandas.io.pytables import read_hdf
dset = read_hdf(ts1.io_manager._output._store, ts1.left_path)
io_manager._output._store.close()
io_manager._input._store.close()
dset['tsvalue_0'].quantile([0,0.1,0.25,0.5])

# Test: state_add_ts(state, ts1.left_path, ts1.default_value)
# inspect:
# - ts1.left_path in state['state_paths'].keys()
# - state['state_paths'][ts1.left_path] = append_state(state['state_ix'], ts1.default_value)
# - var_ix = get_state_ix(state['state_ix'], state['state_paths'], ts1.left_path)

# is the same as:
# - ts = precip_ts.io_manager.read_ts(Category.INPUTS, None, precip_ts.ts_name)
# - ts = transform(ts, precip_ts.ts_name, 'SAME', precip_ts.siminfo)
# - ts = precip_ts.io_manager.read_ts(Category.INPUTS, None, precip_ts.ts_name).columns
# - ts = np.transpose(ts)[0]

