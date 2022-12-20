"""
The class ModelObject is the base class upon which all other dynamic model objects are built on.
It handles all Dict management functions, but provides for no runtime execution of it's own.
All runtime exec is done by child classes.
"""
from HSP2.utilities_specl import *
class ModelObject:
    state_ix = {} # Shared Dict with the numerical state of each object 
    state_paths = {} # Shared Dict with the hdf5 path of each object 
    dict_ix = {} # Shared Dict with the hdf5 path of each object 
    op_tokens = {} # Shared Dict with the tokenized representation of each object 
    
    def __init__(self, name, container = False):
        self.name = name
        self.container = container # will be a link to another object
        self.log_path = "" # Ex: "/RESULTS/RCHRES_001/SPECL" 
        self.attribute_path = "/OBJECTS/RCHRES_001" # 
        self.state_path = "" # Ex: "/STATE/RCHRES_001" # the pointer to this object state
        self.inputs = {} # associative array with key=local_variable_name, value=hdf5_path Ex: [ 'Qin' : '/STATE/RCHRES_001/IVOL' ]
        self.inputs_ix = {} # associative array with key=local_variable_name, value=state_ix integer key
        self.ix = False
        self.default_value = 0.0
        self.ops = []
        self.optype = 0 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - ?
    
    def load_state_dicts(op_tokens, state_paths, state_ix, dict_ix):
        self.op_tokens = op_tokens
        self.state_paths = state_paths
        self.state_ix = state_ix
        self.dict_ix = dict_ix
    
    def make_state_path(self):
        if not (self.container == False):
            self.state_path = self.container.state_path + "/" + self.name
        else:
            self.state_path = "/STATE/" + self.name
        return self.state_path
    
    def find_var_path(self, var_name):
        if var_name in self.inputs_ix.keys():
            return self.inputs_ix[var_name]
        if not (self.container == False):
            print(self.name,"looking to parent", self.container.name, "for", var_name)
            self.container.find_var_path(var_name)
        print(self.name, "could not find", var_name)
        return False
    
    def register_path(self):
        # initialize the path variable if not already set
        if self.state_path == '':
            self.make_state_path()
        self.ix = set_state(self.state_ix, self.state_paths, self.state_path, self.default_value)
        # this should check to see if this object has a parent, and if so, register the name on the parent 
        # as an input?
        if not (self.container == False):
            return self.container.add_input(self.name, self.state_path)
        return self.ix
    
    def add_input(self, var_name, var_path):
        # this will add to the inputs, but also insure that this 
        # requested path gets added to the state/exec stack via an input object if it does 
        # not already exist.
        self.inputs[var_name] = var_path
        self.inputs_ix[var_name] = self.insure_path(var_path)
        return self.inputs_ix[var_name]
    
    def insure_path(self, var_path):
        # if this path can be found in the hdf5 make sure that it is registered in state
        # and that it has needed object class to render it at runtime (some are automatic)
        # RIGHT NOW THIS DOES NOTHING TO CHECK IF THE VAR EXISTS THIS MUST BE FIXED
        var_ix = set_state(self.state_ix, self.state_paths, var_path, 0.0)
        return var_ix 
    
    def get_state(self):
        return self.state_ix[self.ix]
    
    def tokenize(self):
        # renders tokens for high speed execution
        self.ops = [self.optype, self.ix]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        if self.ops == []:
            self.tokenize()
        print(self.name, "tokens", self.ops)
        self.op_tokens[self.ix] = np.asarray(self.ops, dtype="i8")


