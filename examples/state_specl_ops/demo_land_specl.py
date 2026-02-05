# Must be run from the HSPsquared source directory, the h5 file has already been setup with hsp import_uci test10.uci
# bare bones tester - must be run from the HSPsquared source directory
import os

import numpy
from hsp2.hsp2.main import *
from hsp2.hsp2.om import *
from hsp2.hsp2io.hdf import HDF5
from hsp2.hsp2io.io import IOManager
from hsp2.state.state import *

h5file = "aopN51730.h5"

hdf5_instance = HDF5(h5file)
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
state["specactions"] = uci_obj.specactions  # stash the specaction dict in state

state_siminfo_hsp2(uci_obj, siminfo)
# Add support for dynamic functions to operate on STATE
# - Load any dynamic components if present, and store variables on objects
state_load_dynamics_hsp2(state, io_manager, siminfo)
# Iterate through all segments and add crucial paths to state
# before loading dynamic components that may reference them
state_init_hsp2(state, opseq, activities)
state_load_dynamics_specl(state, io_manager, siminfo)  # traditional special actions
state_load_dynamics_om(
    state, io_manager, siminfo
)  # operational model for custom python
state_om_model_run_prep(
    state, io_manager, siminfo
)  # this creates all objects from the UCI and previous loads
# state['model_root_object'].find_var_path('RCHRES_R001')
# Get the timeseries naked, without an object
Rlocal = state["model_object_cache"]["/STATE/RCHRES_R001/Rlocal"]
Rlocal_ts = Rlocal.read_ts()
rchres1 = state["model_object_cache"]["/STATE/RCHRES_R001"]
