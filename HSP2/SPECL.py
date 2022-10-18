''' process special actions in this domain

CALL: specl(ui, ts, step, specactions)
    ui is a dictionary with RID specific HSPF UCI like data
    ts is a dictionary with RID specific timeseries
    step is the current simulation step
    specactions is a dictionary with all SPEC-ACTIONS entries
'''

from numba import njit

@njit
def specl(ui, ts, step, specactions):
    print("specl()")

    # call _specl_()
    ts = _specl_(ui, ts, step, specactions)
    
    # return errors, ERRMSGS


@njit
def _specl_(ui, ts, step, specactions):
    print("_specl_()")
    
    # example for modifying ts element
    # ts['OUTDGT2'][step] = 99

    # return errors
    