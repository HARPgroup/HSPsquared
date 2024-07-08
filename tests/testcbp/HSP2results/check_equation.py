# Must be run from the HSPsquared source directory, the h5 file has already been setup with hsp import_uci test10.uci
# bare bones tester - must be run from the HSPsquared source directory
# Note: First time you clone git, or after a major refactor, you must reinstall (in a venv) using:
#   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --default-timeout=100 -e . 
import os
from hsp2.hsp2.main import *
from hsp2.hsp2.om import *
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

io_manager = IOManager(hdf5_instance)
uci_obj = io_manager.read_uci()
siminfo = uci_obj.siminfo
opseq = uci_obj.opseq
# Note: now that the UCI is read in and hdf5 loaded, you can see things like:
# - hdf5_instance._store.keys() - all the paths in the UCI/hdf5
# - finally stash specactions in state, not domain (segment) dependent so do it once
# now load state and the special actions
state = init_state_dicts()
om_init_state(state)
state['specactions'] = uci_obj.specactions # stash the specaction dict in state

state_siminfo_hsp2(uci_obj, siminfo)
# Add support for dynamic functions to operate on STATE
# - Load any dynamic components if present, and store variables on objects
state_load_dynamics_hsp2(state, io_manager, siminfo)
# Iterate through all segments and add crucial paths to state
# before loading dynamic components that may reference them
state_init_hsp2(state, opseq, activities)
specl_load_state(state, io_manager, siminfo) # traditional special actions
state_load_dynamics_om(state, io_manager, siminfo) # operational model for custom python
state_om_model_run_prep(state, io_manager, siminfo)

# run the simulation
from hsp2.hsp2tools.commands import import_uci, run
run(fpath, saveall=True, compress=False)
# Now, load the timeseries from hdf5 and check the values from the simulation.
from pandas import read_hdf
hydr_path = '/RESULTS/RCHRES_R001/HYDR'
HYDR_ts = read_hdf(io_manager._output._store, hydr_path)
# Note, in order to run from cmd prompt in another window, may need to close the h5:
#    io_manager._output._store.close()
#    io_manager._input._store.close()
Qout = HYDR_ts['OVOL3']*12.1 #Qout in units of cfs
wd = HYDR_ts['O1'] + HYDR_ts['O2']
Qout.quantile([0,0.1,0.5,0.75,0.9,1.0])
Qout.mean()
wd.quantile([0,0.1,0.5,0.75,0.9,1.0])
wd.mean()
