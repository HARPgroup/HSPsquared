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
def specl(ui, ts, OUTDGT, step, specactions):

    errors_specl = _specl_(ui, ts, OUTDGT, step, specactions)
    
    return errors_specl


@njit
def _specl_(ui, ts, OUTDGT, step, specactions):
    # todo determine best way to do error handling in specl
    errors_specl = zeros(int(1)).astype(int64)

    # print("OUTDGT[step, :]", OUTDGT[step, 0]) # returns first item
    # print("OUTDGT[step, :]", OUTDGT[step, :]) # returns all 3 items
    # OUTDGT[step] = [99, 99, 0.0]
    # print(OUTDGT[step, 0])

    # print("MYTEST[step, :]", [OUTDGT[step, 0] - 99, OUTDGT[step, 1], OUTDGT[step, 2]])
    # OUTDGT[step, :] = [OUTDGT[step, 0], OUTDGT[step, 1], OUTDGT[step, 2]]
    OUTDGT[step, 0] = 99
    # print("OUTDGT[step, :]", OUTDGT[step, :])

    # ts['OUTDGT1'][step] = 99
    # print("  ts['OUTDGT1'][step]", ts['OUTDGT1'][step])
    # print("  ts['OUTDGT2'][step]", ts['OUTDGT2'][step])

    # print("OUTDGT[step, :]", OUTDGT[step, :]) 
    return errors_specl  