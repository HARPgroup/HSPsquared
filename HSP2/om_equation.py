"""
The class Equation is used to translate an equation in text string form into a tokenized model op code
The equation will look for variable names inside the equation string (i.e. not numeric, not math operator)
and will then search the local object inputs and the containing object inputs (if object has parent) for 
the variable name in question.  Ultimately, everyting becomes either an operator or a reference to a variable
in the state_ix Dict for runtime execution.
"""
from HSP2.model_object import ModelObject
from numba import njit
class Equation(ModelObject):
    # the following are supplied by the parent class: name, log_path, attribute_path, state_path, inputs
    
    def __init__(self, name, container = False, eqn = ""):
        super(Equation, self).__init__(name, container)
        self.equation = eqn
        self.ps = False 
        self.var_ops = [] # keep these separate since the equation functions should not have to handle overhead
        self.optype = 1 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - ?
    
    def deconstruct_eqn(self):
        exprStack = []
        exprStack[:] = []
        self.ps = deconstruct_equation(self.equation)
        print(exprStack)
    
    def tokenize_ops(self):
        self.deconstruct_eqn()
        self.var_ops = tokenize_ops(self.ps)
    
    def tokenize_vars(self):
      # now stash the string vars as new state vars
      for j in range(2,len(self.var_ops)):
          if isinstance(self.var_ops[j], int):
              continue # already has been tokenized, so skip ahead
          elif is_float_digit(self.var_ops[j]):
              # must add this to the state array as a constant
              constant_path = self.state_path + '/_ops/_op' + str(j) 
              s_ix = set_state(self.state_ix, self.state_paths, constant_path, float(self.var_ops[j]) )
              self.var_ops[j] = s_ix
          else:
              # this is a variable, must find it's data path index
              var_path = self.find_var_path(self.var_ops[j])
              s_ix = get_state_ix(self.state_ix, self.state_paths, var_path)
              if s_ix == False:
                  print("Error: unknown variable ", self.var_ops[j])
                  return
              else:
                  self.var_ops[j] = s_ix
    
    def tokenize(self):
        self.tokenize_ops() 
        self.tokenize_vars()
        # renders tokens for high speed execution
        self.ops = [self.optype, self.ix] + self.var_ops

@njit
def exec_eqn(op_token, state_ix):
    op_class = op_token[0] # we actually will use this in the calling function, which will decide what 
                      # next level function to use 
    result = 0
    num_ops = op_token[2]
    s = np.array([0.0])
    s_ix = -1 # pointer to the top of the stack
    s_len = 1
    #print(num_ops, " operations")
    for i in range(num_ops): 
        op = op_token[3 + 3*i]
        t1 = op_token[3 + 3*i + 1]
        t2 = op_token[3 + 3*i + 2]
        # if val1 or val2 are < 0 this means they are to come from the stack
        # if token is negative, means we need to use a stack value
        #print("s", s)
        if t1 < 0: 
            val1 = s[s_ix]
            s_ix -= 1
        else:
            val1 = state_ix[t1]
        if t2 < 0: 
            val2 = s[s_ix]
            s_ix -= 1
        else:
            val2 = state_ix[t2]
        #print(s_ix, op, val1, val2)
        if op == 1:
            #print(val1, " - ", val2)
            result = val1 - val2
        elif op == 2:
            #print(val1, " + ", val2)
            result = val1 + val2
        elif op == 3:
            #print(val1, " * ", val2)
            result = val1 * val2 
        elif op == 4:
            #print(val1, " / ", val2)
            result = val1 / val2 
        elif op == 5:
            #print(val1, " ^ ", val2)
            result = pow(val1, val2) 
        s_ix += 1
        if s_ix >= s_len: 
            s = np.append(s, 0)
            s_len += 1
        s[s_ix] = result
    result = s[s_ix]
    return result 