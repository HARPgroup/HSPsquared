''' process special actions in this domain
CALL: specl(ui, ts, step, specactions)
    ui is a dictionary with RID specific HSPF UCI like data
    ts is a dictionary with RID specific timeseries
    step is the current simulation step
    specactions is a dictionary with all SPEC-ACTIONS entries
'''

from numba import njit
from numpy import zeros, any, full, nan, array, int64

@njit
# def specl(ui, ts, state, step, specactions):
def specl(ui, ts, state_ix, step):

    # errors_specl = _specl_(ui, ts, state, step, specactions)
    errors_specl = _specl_(ui, ts, state_ix, step)
    
    return errors_specl


@njit
# def _specl_(ui, ts, state, step, specactions):
def _specl_(ui, ts, state_ix, step):
    # todo determine best way to do error handling in specl
    errors_specl = zeros(int(1)).astype(int64)

    # state[1] = state[1] + 1000
    state_ix[1] += 1000
    state_ix[2] = 99
    # state[3]

    return errors_specl  