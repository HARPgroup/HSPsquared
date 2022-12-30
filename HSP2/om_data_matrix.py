"""
The class DataMatrix is used to translate provide table lookup and interpolation function.
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
"""
from HSP2.om_model_object import ModelObject
from HSP2.om_constant import *
from HSP2.utilities_specl import *
from numba import njit
import numpy as np

class DataMatrix(ModelObject):
    def __init__(self, name, container = False, matrix_vals = []):
        super(DataMatrix, self).__init__(name, container)
        self.matrix = matrix_vals # gets passed in at creation.  Refers to path "/OBJECTS/DataMatrix/RCHRES_0001/stage_storage_discharge/matrix"
        self.optype = 2 # 0 - shell object, 1 - equation, 2 - DataMatrix, 3 - input, 4 - broadcastChannel, 5 - ?
        self.nrows = self.matrix.shape[0]
        self.ncols = self.matrix.shape[1]
        # tokenized version of the matrix with variable references and constant references
        self.matrix_tokens = []
        # set of default values to populate dict_ix
        self.matrix_values = np.zeros(self.matrix.shape)
        self.find_paths()
    
    def find_paths(self, trust = False):
        for i in range(self.nrows):
            for j in range(self.ncols):
                self.matrix_tokens.append( self.constant_or_path(self.matrix[i][j], 'rowcol_' + str(i) + "_" + str(j)) )
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        # - insure we have a entity_ix pointing to state_ix
        # - check matrix for string vars and get entity_ix for string variables 
        # - add numerical constants to the state_ix and get the resulting entity_ix
        # - format array of all rows and columns state_ix references 
        # - store array in dict_ix keyed with entity_ix
        # - get entity_ix for lookup key(s)
        # - create tokenized array with entity_ix, lookup types, 
        # renders tokens for high speed execution
        self.ops = self.ops + [self.nrows, self.ncols] + self.matrix_tokens
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()
        self.dict_ix[self.ix] = DataFrame(self.matrix_values).to_numpy()


class DataMatrixLookup(ModelObject):
    def __init__(self, name, container, matrix_path, mx_type, key1, lu_type1, key2, lu_type2, default_value = 0.0):
        super(DataMatrixLookup, self).__init__(name, container)
        self.matrix_path = matrix_path # gets passed in at creation.  Refers to path "/OBJECTS/DataMatrix/RCHRES_0001/stage_storage_discharge/matrix"
        # self.op_matrix = [] # this is the final opcoded matrix for runtime
        self.optype = 8 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - Constant (numeric), 8 - matrix accessor
        self.add_input('matrix', matrix_path, False)
        self.key1_ix = self.constant_or_path(key1, 'key1')
        self.key2_ix = self.constant_or_path(key2, 'key2')
        matrix = self.get_dict_state(self.inputs_ix['matrix'])
        self.nrows = matrix.shape[0]
        self.ncols = matrix.shape[1]
        # mx_type = 0: no lookup, matrix, 1: 1d (default to col 2 as value), 2: 2d (both ways), 3: 1.5d (keyval2 = column index) 
        #  - 1d: look up row based on column 0, return value from column 1
        #  - 1.5d: look up/interp row based on column 0, return value from column 
        #  - 2d: look up based on row and column 
        # lu_type: 0 - exact match; 1 - interpolate values; 2 - stair step
        self.mx_type = mx_type # 1, 2 or 1.5 are supported, type 0 is NOT (at the moment, but can access the array from dict_ix)
        self.lu_type1 = lu_type1
        self.lu_type2 = lu_type2
        self.default_ix = 0
        # tokenized version of the matrix with variable references and constant references
        self.matrix_tokens = np.zeros(self.nrows * self.ncols, dtype=int ) 
        # set of default values to populate dict_ix
        self.matrix_values = np.zeros(matrix.shape)
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
        self.ops = self.ops + [self.inputs_ix['matrix'], self.mx_type, self.nrows, self.ncols, self.key1_ix, self.lu_type1, self.key2_ix, self.lu_type2 ]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()


# njit functions for runtime

@njit
def om_table_lookup(data_table, mx_type, ncols, keyval1, lu_type1, keyval2, lu_type2):
    # mx_type = 0: no lookup, matrix, 1: 1d (default to col 2 as value), 2: 2d (both ways), 3: 1.5d (keyval2 = column index) 
    #  - 1: 1d, look up row based on column 0, return value from column 1
    #  - 2: 2d, look up based on row and column 
    #  - 3: 1.5d, look up/interp row based on column 0, return value from column 
    # lu_type: 0 - exact match; 1 - interpolate values; 2 - stair step
    if mx_type == 1:
        valcol = int(1)
        luval = table_lookup(data_table, keyval1, lu_type1, valcol)
        return luval
    if ( (mx_type == 3) or (lu_type2 == 0) ): # 1.5d (a 2-d with exact match column functions just like a 1.5d )
        valcol = int(keyval2)
        luval = table_lookup(data_table, keyval1, lu_type1, valcol)
        return luval
    # must be a 2-d lookup 
    # if lu_type1 is stair step or exact match, we call the whole row 
    if (lu_type1 == 2):
        row_vals = table_row_lookup(data_table, keyval1, lu_type1)
    elif (lu_type1 == 0):
        row_vals = table_row_lookup(data_table, keyval1, lu_type1)
    else:
        # create an interpolated version of the table 
        row_vals = row_interp(data_table, ncols, keyval1, lu_type1)
        # have to use row zero as the keys for row_vals now cause we will interpolate on those
    row_keys = data_table[0]
    # 1: get value for all columns based on the row interp/match type 
    luval = np.interp(keyval2, row_keys, row_vals)
    # show value at tis point
    return luval

@njit 
def row_interp(data_table, ncols, keyval, lu_type):
    row_vals = data_table[0].copy() # initialize to the first row 
    print("interping for keyval", keyval, "lutype:", lu_type, "ncols", ncols, "in table", data_table)
    for i in range(ncols):
        row_vals[i] = table_lookup(data_table, keyval, lu_type, i)
    return row_vals

@njit
def table_row_lookup(data_table, keyval, lu_type):
    print("looking for keyval", keyval, "lutype:", lu_type, "in table", data_table)
    if (lu_type == 2):
        # stair step retrieve whole row 
        idx = (data_table[:, 0][0:][(data_table[:, 0][0:]- keyval) <= 0]).argmax()
    elif (lu_type == 0):
        idx = int(keyval)
    print("looking for row", idx, "in table", data_table)
    row_vals = data_table[:][0:][idx]
    return row_vals

@njit
def table_lookup(data_table, keyval, lu_type, valcol):
    if lu_type == 2: #stair-step
        idx = (data_table[:, 0][0:][(data_table[:, 0][0:]- keyval) <= 0]).argmax()
        luval = data_table[:, valcol][0:][idx]
    elif lu_type == 1: # interpolate
        luval = np.interp(keyval,data_table[:, 0][0:], data_table[:, valcol][0:])
    
    # show value at this point
    return luval

@njit
def exec_tbl_values(op, state_ix, dict_ix):
    ix = op[1]
    matrix = dict_ix[ix]
    nrows = op[2]
    ncols = op[3]
    k = 0
    for i in range(nrows):
        for j in range(ncols):
            matrix[i][j] = state_ix[op[4 + k]]
            k = k + 1
    dict_ix[ix] = matrix 
    return 0.0

@njit
def exec_tbl_eval(op_tokens, op, state_ix, dict_ix):
    # Note: these indices must be adjusted to reflect the number of common op tokens
    # check this first, if it is type = 0, then it is just a matrix, and only needs to be loaded, not evaluated
    ix = op[1]
    dix = op[2]
    # load the attributes for the data matrix that we are accessing
    tbl_op = op_tokens[dix]
    mx_type = op[3] # not used yet, what type of table?  in past this was always 1-d or 2-d 
    nrows = tbl_op[4]
    ncols = tbl_op[5]
    key1_ix = op[6]
    #print("ix, dict_ix, mx_type, key1_ix", ix, dix, mx_type, key1_ix)
    lu_type1 = op[7]
    key2_ix = op[8]
    lu_type2 = op[9]
    data_table = dict_ix[dix]
    keyval1 = state_ix[key1_ix]
    keyval2 = state_ix[key2_ix]
    #print("keyval1, lu_type1, keyval2, lu_type2", keyval1, lu_type1, keyval2, lu_type2)
    result = om_table_lookup(data_table, mx_type, ncols, keyval1, lu_type1, keyval2, lu_type2)
    return result
