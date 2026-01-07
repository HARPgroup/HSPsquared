# null function to be loaded when not supplied by user
from numba import njit  # import the types
from numba.typed import Dict
from numba import types  # import the types

state = {}  # shared state Dictionary, contains numba-ready Dicts
state["state_paths"] = Dict.empty(
    key_type=types.unicode_type, value_type=types.int64
)
state["state_ix"] = Dict.empty(key_type=types.int64, value_type=types.float64)
state["dict_ix"] = Dict.empty(key_type=types.int64, value_type=types.float64[:, :])
state["ts_ix"] = Dict.empty(key_type=types.int64, value_type=types.float64[:])
# initialize state for hydr
# add a generic place to stash model_data for dynamic components
state["model_data"] = {}

@njit
def state_step_hydr(state_info, state_paths, state_ix, dict_ix, ts_ix, hydr_ix, step):
    return
