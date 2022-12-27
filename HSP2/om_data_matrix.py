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
        # self.op_matrix = [] # this is the final opcoded matrix for  runtime
        self.optype = 2 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
    
    def tokenize(self):
        # - insure we have a entity_ix pointing to state_ix
        # - check matrix for string vars and get entity_ix for string variables 
        # - add numerical constants to the state_ix and get the resulting entity_ix
        # - format array of all rows and columns state_ix references 
        # - store array in dict_ix keyed with entity_ix
        # - get entity_ix for lookup key(s)
        # - create tokenized array with entity_ix, lookup types, 
        # renders tokens for high speed execution
        self.ops = [self.optype, self.ix]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()
        self.dict_ix[self.ix] = self.op_matrix.to_numpy()

# njit functions for runtime

@njit
def om_table_lookup(data_table, mx_type, keyval1, lutype1, keyval2, lutype2):
    # mx_type = 1d, 1.5d, 2d
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
    # 1: get value for all columns based on the row interp/match type 
    if lutype == 2: #stair-step
        idx = (data_table[:, 0][0:][(data_table[:, 0][0:]- keyval1) <= 0]).argmax()
        luval = data_table[:, valcol][0:][idx]
    elif lutype == 1: # interpolate
        luval = np.interp(keyval1,data_table[:, 0][0:], data_table[:, valcol][0:])
        
    # show value at tis point
    return luval


@njit
def specl_lookup(data_table, keyval, lutype, valcol):
    if lutype == 2: #stair-step
        idx = (data_table[:, 0][0:][(data_table[:, 0][0:]- keyval) <= 0]).argmax()
        luval = data_table[:, valcol][0:][idx]
    elif lutype == 1: # interpolate
        luval = np.interp(keyval,data_table[:, 0][0:], data_table[:, valcol][0:])
        
    # show value at tis point
    return luval

@njit
def exec_tbl_eval(op, state_ix, dict_ix):
    ix = op[1]
    dix = op[2]
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