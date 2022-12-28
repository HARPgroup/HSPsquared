"""
The class DataMatrix is used to translate provide table lookup and interpolation function.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
from numba import njit
class DataMatrix(ModelObject):
    def __init__(self, name, container = False, matrix_vals = []):
        super(DataMatrix, self).__init__(name, container)
        self.lu_type1 = ""
        self.matrix = matrix_vals # gets passed in at creation.  Refers to path "/OBJECTS/DataMatrix/RCHRES_0001/stage_storage_discharge/matrix"
        # we need to check these matrix_vals because the OM system allowed 
        # column headers to be put into the first row as placeholders, and 
        # if those string variables did NOT resolve to something in state it would simply 
        # ignore them, which is sloppy.  So, we should check for the first column and row 
        # if it is text, we will assume that it uses this data convention and eliminate the row 
        # this is a problem because this facility ALSO was used to supply dynamic names 
        # For example, in the Rivanna simulation 
        # tier4_balance_demand (see http://deq1.bse.vt.edu:81/d.dh/om-model-info/5828517 )
        # Auto-Set Parent Vars  = 1 (true)
        # the first row had column names: Comp-Mode Wnf Wrm Wsh Wsf
        # the system ignored the 0th column, and created the variables at runtime:
        #    tier4_balance_demand_Wnf tier4_balance_demand_Wrm tier4_balance_demand_Wsh tier4_balance_demand_Wsf
        # this is a useful system, tho, a matrix accessor would be fine replacement for this and cleaner
        # todo: at parse time, we can create these variables as children on this object
        # self.op_matrix = [] # this is the final opcoded matrix for runtime
        self.optype = 2 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
    
    def tokenize(self):
        # cxall parent method to set basic ops common to all 
        super().tokenize()
        # - insure we have a entity_ix pointing to state_ix
        # - check matrix for string vars and get entity_ix for string variables 
        # - add numerical constants to the state_ix and get the resulting entity_ix
        # - format array of all rows and columns state_ix references 
        # - store array in dict_ix keyed with entity_ix
        # - get entity_ix for lookup key(s)
        # - create tokenized array with entity_ix, lookup types, 
        # renders tokens for high speed execution
        self.ops = self.ops + []
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()
        self.dict_ix[self.ix] = self.op_matrix.to_numpy()

# njit functions for runtime

@njit
def om_table_lookup(data_table, mx_type, ncols, keyval1, lutype1, keyval2, lutype2):
    # mx_type = 0: no lookup, matrix, 1: 1d (default to col 2 as value), 2: 2d (both ways), 3: 1.5d (keyval2 = column index) 
    #  - 1d: look up row based on column 0, return value from column 1
    #  - 1.5d: look up/interp row based on column 0, return value from column 
    #  - 2d: look up based on row and column 
    # lutype: 0 - exact match; 1 - interpolate values; 2 - stair step
    if mx_type == 1:
        valcol = 1
        luval = specl_lookup(data_table, keyval1, lutype1, valcol)
        return luval
    if ( (mx_type == 3) or (lutype2 == 0) ): # 1.5d (a 2-d with exact match column functions just like a 1.5d )
        valcol = keyval2
        luval = specl_lookup(data_table, keyval1, lutype1, valcol)
        return luval
    # must be a 2-d lookup 
    # if lutype1 is stair step or exact match, we call specl_lookup with valco = -1, which returns the whole row 
    if (lutype1 == 2):
        row_vals = specl_lookup(data_table, keyval1, lutype1, -1)
    elif (lutype1 == 0):
        row_vals = specl_lookup(data_table, keyval1, lutype1, -1)
    else:
        # create an interpolated version of the table 
        row_vals = row_interp(data_table, ncols, keyval1, lutype1)
        # have to use row zero as the keys for row_vals now cause we will interpolate on those
    row_keys = data_table[0]
    # 1: get value for all columns based on the row interp/match type 
    luval = np.interp(keyval2, row_keys, row_vals)
    # show value at tis point
    return luval

@njit 
def row_interp(data_table, ncols, keyval1, lutype1):
    row_vals = data_table[0].copy() # initialize to the first row 
    for i in range(ncols):
        row_vals[i] = specl_lookup(data_table, keyval1, lutype1, i)
    return row_vals

@njit
def specl_lookup(data_table, keyval, lutype, valcol):
    if lutype == 2: #stair-step
        idx = (data_table[:, 0][0:][(data_table[:, 0][0:]- keyval) <= 0]).argmax()
        if valcol == -1: # whole row requested 
            luval = data_table[:][0:][idx]
        else:
            luval = data_table[:, valcol][0:][idx]
    elif lutype == 1: # interpolate
        luval = np.interp(keyval,data_table[:, 0][0:], data_table[:, valcol][0:])
    
    # show value at this point
    return luval

@njit
def exec_tbl_eval(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
    # these indices must be adjusted to reflect the number of common op tokens
    mx_type = op[3] # not used yet, what type of table?  in past this was always 1-d or 2-d 
    key1_ix = op[4]
    #print("ix, dict_ix, mx_type, key1_ix", ix, dix, mx_type, key1_ix)
    lutype = op[5]
    valcol = op[8]
    data_table = dict_ix[dix]
    keyval = state_ix[key1_ix]
    #print("Key, ltype, val", keyval, lutype, valcol)
    result = specl_lookup(data_table, keyval, lutype, valcol)
    return result