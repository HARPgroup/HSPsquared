"""
The class Equation is used to translate an equation in text string form into a tokenized model op code
The equation will look for variable names inside the equation string (i.e. not numeric, not math operator)
and will then search the local object inputs and the containing object inputs (if object has parent) for 
the variable name in question.  Ultimately, everyting becomes either an operator or a reference to a variable
in the state_ix Dict for runtime execution.
"""
from HSP2.om_model_object import ModelObject
from HSP2.utilities_specl import *
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
                  print("Error: unknown variable ", self.var_ops[j], "path", var_path, "index", s_ix)
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

from pyparsing import (
    Literal,
    Word,
    Group,
    Forward,
    alphas,
    alphanums,
    Regex,
    ParseException,
    CaselessKeyword,
    Suppress,
    delimitedList,
)
import math
import operator

exprStack = []


def push_first(toks):
    exprStack.append(toks[0])


def push_unary_minus(toks):
    for t in toks:
        if t == "-":
            exprStack.append("unary -")
        else:
            break

def deconstruct_equation(eqn):
    """
    We should get really good at using docstrings...

    we parse the equation during readuci/pre-processing and break it into njit'able pieces
    this forms the basis of our object parser code to run at import_uci step 
    """
    results = BNF().parseString(eqn, parseAll=True)
    ps = []
    ep = exprStack
    pre_evaluate_stack(ep[:], ps)
    return ps

def tokenize_ops(ps):
    '''Translates a set of string operands into integer keyed tokens for faster execution.''' 
    tops = [len(ps)] # first token is number of ops
    for i in range(len(ps)):
        if ps[i][0] == '-': op = 1
        if ps[i][0] == '+': op = 2
        if ps[i][0] == '*': op = 3
        if ps[i][0] == '/': op = 4
        if ps[i][0] == '^': op = 5
        # a negative op code indicates null
        # this should cause no confusion since all op codes are references and none are actual values
        if ps[i][1] == None: o1 = -1 
        else: o1 = ps[i][1]
        if ps[i][2] == None: o2 = -1 
        else: o2 = ps[i][2]
        tops.append(op)
        tops.append(o1)
        tops.append(o2)
    return tops

bnf = None


def BNF():
    """
    expop   :: '^'
    multop  :: '*' | '/'
    addop   :: '+' | '-'
    integer :: ['+' | '-'] '0'..'9'+
    atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
    factor  :: atom [ expop factor ]*
    term    :: factor [ multop factor ]*
    expr    :: term [ addop term ]*
    """
    global bnf
    if not bnf:
        # use CaselessKeyword for e and pi, to avoid accidentally matching
        # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
        # and CaselessKeyword only match whole words
        e = CaselessKeyword("E")
        pi = CaselessKeyword("PI")
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        ident = Word(alphas, alphanums + "_$")
        
        plus, minus, mult, div = map(Literal, "+-*/")
        lpar, rpar = map(Suppress, "()")
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        
        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        def insert_fn_argcount_tuple(t):
            fn = t.pop(0)
            num_args = len(t[0])
            t.insert(0, (fn, num_args))
        
        fn_call = (ident + lpar - Group(expr_list) + rpar).setParseAction(
            insert_fn_argcount_tuple
        )
        atom = (
            addop[...]
            + (
                (fn_call | pi | e | fnumber | ident).setParseAction(push_first)
                | Group(lpar + expr + rpar)
            )
        ).setParseAction(push_unary_minus)
        
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= atom + (expop + factor).setParseAction(push_first)[...]
        term = factor + (multop + factor).setParseAction(push_first)[...]
        expr <<= term + (addop + term).setParseAction(push_first)[...]
        bnf = expr
    return bnf


# map operator symbols to corresponding arithmetic operations
epsilon = 1e-12
opn = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}

fn = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "abs": abs,
    "trunc": int,
    "round": round,
    "sgn": lambda a: -1 if a < -epsilon else 1 if a > epsilon else 0,
    # functionsl with multiple arguments
    "multiply": lambda a, b: a * b,
    "hypot": math.hypot,
    # functions with a variable number of arguments
    "all": lambda *a: all(a),
}

fns = {
    "sin": "math.sin",
    "cos": "math.cos",
    "tan": "math.tan",
    "exp": "math.exp",
    "abs": "abs",
    "trunc": "int",
    "round": "round",
}


def evaluate_stack(s):
    op, num_args = s.pop(), 0
    if isinstance(op, tuple):
        op, num_args = op
    if op == "unary -":
        return -evaluate_stack(s)
    if op in "+-*/^":
        # note: operands are pushed onto the stack in reverse order
        op2 = evaluate_stack(s)
        op1 = evaluate_stack(s)
        return opn[op](op1, op2)
    elif op == "PI":
        return math.pi  # 3.1415926535
    elif op == "E":
        return math.e  # 2.718281828
    elif op in fn:
        # note: args are pushed onto the stack in reverse order
        args = reversed([evaluate_stack(s) for _ in range(num_args)])
        return fn[op](*args)
    elif op[0].isalpha():
        raise Exception("invalid identifier '%s'" % op)
    else:
        # try to evaluate as int first, then as float if int fails
        try:
            return int(op)
        except ValueError:
            return float(op)

def pre_evaluate_stack(s, ps):
    op, num_args = s.pop(), 0
    if isinstance(op, tuple):
        op, num_args = op
    if op == "unary -":
        ps.append([-evaluate_stack(s), 0, 0])
        return 
    if op in "+-*/^":
        # note: operands are pushed onto the stack in reverse order
        op2 = pre_evaluate_stack(s, ps)
        op1 = pre_evaluate_stack(s, ps)
        ps.append([ op, op1, op2])
        return 
    elif op == "PI":
        ps.append([math.pi, 0, 0])  # 3.1415926535
        return 
    elif op == "E":
        ps.append([math.e, 0, 0])  # 2.718281828
        return 
    elif op in fns:
        # note: args are pushed onto the stack in reverse order
        print("s:", s, "op", op)
        args = []
        for x in range(num_args):
            args.append(pre_evaluate_stack(s, ps))
        args.reverse()
        args.insert(fns[op], 0)
        ps.append(args)
        return 
    elif op[0].isalpha():
        return op
    else:
        # return the operand now
        return op
