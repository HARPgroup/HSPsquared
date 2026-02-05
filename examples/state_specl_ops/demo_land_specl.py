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

# read user control, parameters, states, and flags parameters and map to local variables
parameter_obj = io_manager.read_parameters()
opseq = parameter_obj.opseq
ddlinks = parameter_obj.ddlinks
ddmasslinks = parameter_obj.ddmasslinks
ddext_sources = parameter_obj.ddext_sources
ddgener = parameter_obj.ddgener
model = parameter_obj.model
siminfo = parameter_obj.siminfo
ftables = parameter_obj.ftables
specactions = parameter_obj.specactions
monthdata = parameter_obj.monthdata

start, stop = siminfo["start"], siminfo["stop"]

copy_instances = {}
gener_instances = {}
# Note: now that the UCI is read in and hdf5 loaded, you can see things like:
state = init_state_dicts()
state_siminfo_hsp2(parameter_obj, siminfo, io_manager, state)
# Add support for dynamic functions to operate on STATE
# - Load any dynamic components if present, and store variables on objects
state_load_dynamics_hsp2(state, io_manager, siminfo)
# Iterate through all segments and add crucial paths to state
# before loading dynamic components that may reference them
state_init_hsp2(state, opseq, activities)
# - finally stash specactions in state, not domain (segment) dependent so do it once
state["specactions"] = specactions  # stash the specaction dict in state
om_init_state(state)  # set up operational model specific state entries
specl_load_state(state, io_manager, siminfo)  # traditional special actions
state_load_dynamics_om(
    state, io_manager, siminfo
)  # operational model for custom python
# finalize all dynamically loaded components and prepare to run the model
state_om_model_run_prep(state, io_manager, siminfo)
#######################################################################################

# state['model_root_object'].find_var_path('RCHRES_R001')
# Get the timeseries naked, without an object
Rlocal = state["model_object_cache"]["/STATE/RCHRES_R001/Rlocal"]
Rlocal_ts = Rlocal.read_ts()
rchres1 = state["model_object_cache"]["/STATE/RCHRES_R001"]
