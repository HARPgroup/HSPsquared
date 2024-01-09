import sys
from numba import int8, float32, njit, types, typed # import the types

print("Loaded a set of  HSP2 code!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

@njit
def state_step_hydr(state_info, state_paths, state_ix, dict_ix, ts_ix, hydr_ix, step):
    state_ix[hydr_ix['O1']] = 10.0 * 1.547
    if ( (state_ix[state_paths['/STATE/year']] == 2020)
       and (state_ix[state_paths['/STATE/month']] == 12)
       and (state_ix[state_paths['/STATE/day']] == 31)
       and (state_ix[state_paths['/STATE/hour']] == 1)
    ):
        print("Custom state_step_hydr() called")
        print("state at start", state_ix)
        print("state_paths", state_paths)
        print("nhd_8567213 Runit", state_ix[state_paths['/STATE/RCHRES_R001/Runit']])
        print("nhd_8567213 Qlocal", state_ix[state_paths['/STATE/RCHRES_R001/nhd_8566779/nhd_8566781/nhd_8567213/Qlocal']])
        print("nhd_8567213 Qtrib", state_ix[state_paths['/STATE/RCHRES_R001/nhd_8566779/nhd_8566781/nhd_8567213/Qtrib']])
        print("Qout", state_ix[state_paths['/STATE/RCHRES_R001/nhd_8566779/nhd_8566781/nhd_8567213/Qout']])
        # since this has been called in the step() function, the Qtrib register in hydroObject/Qtrib
        # has been cleared, and this is called before the json objects have been exec'ed, so this 
        # should print out to zero
        print("parent Qtrib", state_ix[state_paths['/STATE/RCHRES_R001/nhd_8566779/nhd_8566781/hydroObject/Qtrib']])
        # this is copied from the above register at then end of the timestep, so it should be filled 
        # with the value from the end of the previous timestep
        print("parent Qtrib", state_ix[state_paths['/STATE/RCHRES_R001/nhd_8566779/nhd_8566781/Qtrib']])
        print("RCHRES_R001 Runit", state_ix[state_paths['/STATE/RCHRES_R001/Runit']])
        print("RCHRES_R001 Qlocal", state_ix[state_paths['/STATE/RCHRES_R001/Qlocal']])
        print("RCHRES_R001 Qtrib", state_ix[state_paths['/STATE/RCHRES_R001/Qtrib']])
        print("RCHRES_R001 trib_area_sqmi", state_ix[state_paths['/STATE/RCHRES_R001/trib_area_sqmi']])
        print("RCHRES_R001 drainage_area_sqmi", state_ix[state_paths['/STATE/RCHRES_R001/drainage_area_sqmi']])
        print("RCHRES_R001 Qout", state_ix[state_paths['/STATE/RCHRES_R001/Qout']])
        print("domain info", state_info)
    return
