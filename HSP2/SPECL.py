''' process special actions in this domain

CALL: specl(ui, ts, step, specactions)
    ui is a dictionary with RID specific HSPF UCI like data
    ts is a dictionary with RID specific timeseries
    step is the current simulation step
    specactions is a dictionary with all SPEC-ACTIONS entries
'''

from numba import njit

@njit(cache=True)
def specl(ui, ts, step, specactions):
    
    test_withdrawal = 99

    # example for modifying ts element
    # ts['OUTDGT2'][step] = test_withdrawal

    # return errors