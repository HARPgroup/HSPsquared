from numpy import array, zeros, where, int64, asarray
from math import log10, exp
from numba import njit, types
from numba.types import List

# the following imports added to handle special actions
from hsp2.hsp2.state import (
    sedtrn_get_ix,
    sedtrn_init_ix,
    get_domain_state,
    set_domain_state,
)
from hsp2.hsp2.om import pre_step_model, step_model, model_domain_dependencies
from numba.typed import Dict


@njit
def step_sedtrn(
    domain,
    state_paths,
    state_ix,
    dict_ix,
    ts_ix,
    op_tokens,
    model_exec_list,
    step,
    ep_list,
):
    # model_exec_list: a list of elements (specl etc.) that influence these SEDTRN end points
    # ep_list = np.asarray(["RSED1", "RSED2", "RSED3", "RSED4", "RSED5", "RSED6"], dtype='U')
    # NOTE: this could be cached in dict_ix
    # call related specl/ops pre-steps, such as loading timeseries values
    pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    # call related specl/ops steps
    step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    # get state value at beginning of timestep - python experts will no doubt have a more code efficient method than this
    sand_rsed1, silt_rsed2, clay_rsed3, sand_wt_rsed4, silt_wt_rsed5, clay_wt_rsed6 = (
        get_domain_state(state_paths, state_ix, domain, ep_list)
    )
    # now, do sedtrn (simplified for demo purposes)
    tsed1 = sand_rsed1 + silt_rsed2 + clay_rsed3
    tsed2 = sand_wt_rsed4 + silt_wt_rsed5 + clay_wt_rsed6
    sand_t_rsed7 = sand_rsed1 + sand_wt_rsed4
    silt_t_rsed8 = silt_rsed2 + silt_wt_rsed5
    clay_t_rsed9 = clay_rsed3 + clay_wt_rsed6
    tsed3 = sand_t_rsed7 + silt_t_rsed8 + clay_t_rsed9
    # pass values back to state
    state_vals = [
        sand_rsed1,
        silt_rsed2,
        clay_rsed3,
        sand_wt_rsed4,
        silt_wt_rsed5,
        clay_wt_rsed6,
    ]
    set_domain_state(state_paths, state_ix, domain, ep_list, state_vals)
    return


@njit
def get_domain_state_str(state_paths, state_str, domain, varkeys):
    # get values for a set of variables in a domain
    # will not check for the index in state_ix, and will fail if a non-scalar value is needed (like from dict_ix)
    # if varkeys = False, assume that we want all the variables
    # from the domain, that are predetermined ahead of time, and should save performance
    ret_vals = zeros(len(varkeys))
    j = 0
    for i in varkeys:
        # var_path = f'{domain}/{i}'
        var_path = domain + "/" + i
        #print(var_path)
        ret_vals[j] = state_str[var_path]
        j += 1
    return ret_vals



@njit
def set_domain_state_str(state_str, domain, varkeys, state_vals):
    # get values for a set of variables in a domain
    # will not check for the index in state_ix, and will fail if a non-scalar value is needed (like from dict_ix)
    # if varkeys = False, assume that we want all the variables
    # from the domain, that are predetermined ahead of time, and should save performance
    j = 0
    for i in varkeys:
        # var_path = f'{domain}/{i}'
        var_path = domain + "/" + i
        # print(var_path)
        state_str[var_path] = state_vals[j]
        j += 1
    return True


@njit
def step_sedtrn_str(
    domain,
    state_paths,
    state_str,state_ix,
    dict_ix,
    ts_ix,
    op_tokens,
    model_exec_list,
    step,
    ep_list,
):
    # model_exec_list: a list of elements (specl etc.) that influence these SEDTRN end points
    # ep_list = np.asarray(["RSED1", "RSED2", "RSED3", "RSED4", "RSED5", "RSED6"], dtype='U')
    # NOTE: this could be cached in dict_ix
    # call related specl/ops pre-steps, such as loading timeseries values
    #pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    # call related specl/ops steps
    step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    # get state value at beginning of timestep - python experts will no doubt have a more code efficient method than this
    sand_rsed1, silt_rsed2, clay_rsed3, sand_wt_rsed4, silt_wt_rsed5, clay_wt_rsed6 = (
        get_domain_state_str(state_paths, state_str, domain, ep_list)
    )
    # now, do sedtrn (simplified for demo purposes)
    tsed1 = sand_rsed1 + silt_rsed2 + clay_rsed3
    tsed2 = sand_wt_rsed4 + silt_wt_rsed5 + clay_wt_rsed6
    sand_t_rsed7 = sand_rsed1 + sand_wt_rsed4
    silt_t_rsed8 = silt_rsed2 + silt_wt_rsed5
    clay_t_rsed9 = clay_rsed3 + clay_wt_rsed6
    tsed3 = sand_t_rsed7 + silt_t_rsed8 + clay_t_rsed9
    # pass values back to state
    state_vals = [
        sand_rsed1,
        silt_rsed2,
        clay_rsed3,
        sand_wt_rsed4,
        silt_wt_rsed5,
        clay_wt_rsed6,
    ]
    set_domain_state_str(state_str, domain, ep_list, state_vals)
    return
