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
    ts_ix = {} # Shared Dict with the hdf5 path of each object 
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
        self.optype = 0 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - Constant (numeric), 8 - matrix accessor
        self.register_path()
    
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
        # check local inputs for name
        if var_name in self.inputs.keys():
            #print("Found", var_name, "on ", self.name, "path=", self.inputs[var_name])
            return self.inputs[var_name]
        # check parent for name
        if not (self.container == False):
            #print(self.name,"looking to parent", self.container.name, "for", var_name)
            return self.container.find_var_path(var_name)
        # check for root state vars STATE + var_name
        if ("/STATE/" + var_name) in self.state_paths.keys():
            return self.state_paths[("/STATE/" + var_name)]
        # check for root state vars
        if var_name in self.state_paths.keys():
            return self.state_paths[var_name]
        #print(self.name, "could not find", var_name)
        return False
    
    def constant_or_path(self, keyval, keyname, trust = False):
        if is_float_digit(keyval):
            # we are given a constant value, not a variable reference 
            print("Creating constant ", keyname, " = ", keyval)
            k = Constant(keyname, self, keyval)
            kix = k.ix
        else:
            print("Adding input ", keyname, " = ", keyval)
            kix = self.add_input(keyname, keyval, trust)
        return kix
    
    def register_path(self):
        # initialize the path variable if not already set
        if self.state_path == '':
            self.make_state_path()
        self.ix = set_state(self.state_ix, self.state_paths, self.state_path, self.default_value)
        # this should check to see if this object has a parent, and if so, register the name on the parent 
        # as an input?
        if not (self.container == False):
            # since this is a request to actually create a new path, we instruct trust = True as last argument
            return self.container.add_input(self.name, self.state_path, True)
        return self.ix
    
    def add_input(self, var_name, var_path, trust = False):
        # this will add to the inputs, but also insure that this 
        # requested path gets added to the state/exec stack via an input object if it does 
        # not already exist.
        # trust = False means fail if the path does not already exist, True means assume it will be OK which is bad policy, except for the case where the path points to an existing location
        self.inputs[var_name] = var_path
        var_ix = self.find_var_path(var_path)
        if var_ix == False:
            if (trust == False):
                raise Exception("Cannot find variable path: " + var_path + " ... process terminated.")
            var_ix = self.insure_path(var_path)
        self.inputs_ix[var_name] = var_ix
        return self.inputs_ix[var_name]
    
    def insure_path(self, var_path):
        # if this path can be found in the hdf5 make sure that it is registered in state
        # and that it has needed object class to render it at runtime (some are automatic)
        # RIGHT NOW THIS DOES NOTHING TO CHECK IF THE VAR EXISTS THIS MUST BE FIXED
        var_ix = set_state(self.state_ix, self.state_paths, var_path, 0.0)
        return var_ix 
    
    def get_state(self, ix = -1):
        if ix >= 0:
            return self.state_ix[ix]
        return self.state_ix[self.ix]
    
    def get_dict_state(self, ix = -1):
        if ix >= 0:
            return self.dict_ix[ix]
        return self.dict_ix[self.ix]
    
    def tokenize(self):
        # renders tokens for high speed execution
        self.ops = [self.optype, self.ix]
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        if self.ops == []:
            self.tokenize()
        #print(self.name, "tokens", self.ops)
        self.op_tokens[self.ix] = np.asarray(self.ops, dtype="i8")
    
    def step(self, step):
        # this tests the model for a single timestep.
        # this is not the method that is used for high-speed runs, but can theoretically be used for 
        # easier to understand demonstrations
        step_model({self.op_tokens[self.ix]}, self.state_ix, self.dict_ix, self.ts_ix, step)
    
    def dddstep_model(op_tokens, state_ix, dict_ix, ts_ix, step):
        for i in op_tokens.keys():
            if op_tokens[i][0] == 1:
                state_ix[i] = exec_eqn(op_tokens[i], state_ix)
            elif op_tokens[i][0] == 2:
                state_ix[i] = exec_tbl_eval(op_tokens[i], state_ix, dict_ix)
            elif op_tokens[i][0] == 3:
                step_model_link(op_tokens[i], state_ix, ts_ix, step)
            elif op_tokens[i][0] == 4:
                return False
            elif op_tokens[i][0] == 5:
                step_sim_timer(op_tokens[i], state_ix, dict_ix, ts_ix, step)
        return 


class Constant(ModelObject):
    def __init__(self, name, container = False, value = 0.0):
        super(Constant, self).__init__(name, container)
        self.optype = 7 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - Constant (numeric)
        self.default_value = value 
        self.register_path() #this is one of the few that register a path by default since there are no contingencies to await
        #set_state(self.state_ix, self.state_paths, self.state_path, self.default_value)
        self.state_ix[self.ix] = self.default_value

