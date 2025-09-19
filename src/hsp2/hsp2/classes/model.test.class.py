import random

# Define the spec for the ModelRCHRES class
# note: we store the float, int, array props on the HandlerRCHRES object for convenience
#       but we could just as easily opt to keep it in a separate location loaded via include
model_test_spec = model_base + model_make_spec(['potev_ix', 'prec_ix', 'ovol_ix'], int32) + model_make_spec(['ovol', 'prec', 'potev'], float64) + model_make_spec(['PREC', 'POTEV'], float64[:])

@jitclass(model_test_spec )
class ModelTEST:
    def __init__(self):
        # Note: no inheritance in jitclass as of py 3.12, so, the following cannot work:
        # super(ModelRCHRES, self).__init__()
        # must copy any base method stuff from ModelBase
        self.path = '' # must initialize
        self.value = 0
        self.state_ix = Dict.empty(key_type=types.int64, value_type=types.float64)
        self.state_paths = Dict.empty(key_type=types.unicode_type, value_type=types.float64)
        self.ts = Dict.empty(key_type=types.unicode_type, value_type=types.float64[:])
        self.st = Dict.empty(key_type=types.unicode_type, value_type=types.float64)
        self.inputs = Dict.empty(key_type=types.unicode_type, value_type=types.int64)
        self.inputs['PREC'] = 1
        self.inputs['POTEV'] = 2
        self.potev_ix = 1
        self.prec_ix = 2
        self.ovol_ix = 3
        self.ovol = 0.0
        return
    
    # explore different ways to store local state values
    # 1. char keyed array of state variables (i.e. self.st['potev'])
    # 2. integer keyed array of state variables (i.e. self.state_ix[self.potev_ix])
    # 3. Named class properties state variables (i.e. self.potev ) - does this process more quickly when using mutliple times?
    # explore different ways to set remote state values
    # 1. integer keyed array of state variables (i.e. self.st['potev'])
    # 2. Named class properties state variables (i.e. self.potev )
    
    def pre_step1(self, step):
        # this is a temporary, all timeseries objects will have a pre_step() function that loads their current
        # value into the state array
        self.get_inputs1(1)
    def get_inputs1(self, step):
        # this is a temporary, all timeseries objects will have a pre_step() function that loads their current
        # value into the state array
        self.potev = self.ts[self.path + '/POTEV'][step]
        self.prec = self.ts[self.path + '/PREC'][step]
    def state_read1(self, step):
        self.potev = self.POTEV[step]
        self.prec = self.PREC[step]
        return
    def exec1(self, step):
        # calculate the values
        result = self.prec - self.potev
        if (result < 0):
            result = 0
        self.ovol = result
    def state_write1(self, step):
        self.state_ix[self.prec_ix] = self.prec
        self.state_ix[self.potev_ix] = self.potev
        self.state_ix[self.ovol_ix] = self.ovol
        return
    def step1(self, step):
        self.pre_step1(step)
        self.state_read1(step)
        self.exec1(step)
        self.state_write1(step)
    
    def get_inputs2(self, step):
        # this is a temporary, all timeseries objects will have a pre_step() function that loads their current
        # value into the state array
        self.state_ix[self.potev_ix] = self.ts[self.path + '/POTEV']
        self.state_ix[self.prec_ix] = self.ts[self.path + '/PREC']
    def state_read2(self, step):
        self.potev = self.state_ix[self.potev_ix]
        self.prec = self.state_ix[self.prec_ix]
        return
    def state_write2(self, step):
        self.state_ix[self.prec_ix] = self.st['PREC']
        self.state_ix[self.potev_ix] = self.st['POTEV']
        return
        
    def exec2(self, step):
        # calculate the values
        result = self.st['PREC'] - self.st['POTEV']
        if result < 0:
            result = 0
        self.ovol = result
    
    def state_read3(self, step):
        self.potev = self.state_paths[self.path + '/POTEV']
        self.prec = self.state_paths[self.path + '/PREC']
        return
    def state_read4(self, step):
        for n in ['POTEV', 'PREC']:
            self.st[n] = self.state_paths[self.path + str(n + 1)]
        return
    def state_read5(self, step):
        for n in ['POTEV', 'PREC']:
            self.st[n] = self.state_ix[self.inputs[n]]
        return
    def state_read6(self, step):
        for n in ['POTEV', 'PREC']:
            self.st[n] = self.ts[self.path + '/' + n]
        return
    
    
        

@njit
def fn_test_step(rchres, step):
    # will need to pass in dt and get all others from the object state memory
    rchres.ovol[0] = rchres.state_ix[ix] * rchres.ROVOL / rchres.RO

steps = 300000
prec = zeros(steps)
potev = zeros(steps)
for i in range(steps):
    prec[i] = random.random()
    potev[i] = prec[i] * random.random()


m = ModelTEST()
m.path = '/RCHRESR001'
ts = m.ts
state_ix = m.state_ix
state_paths = m.state_paths
ts['/RCHRESR001/PREC'] = prec
ts['/RCHRESR001/POTEV'] = potev
m.ts = ts 

m.POTEV = ts['/RCHRESR001/POTEV']
m.PREC = ts['/RCHRESR001/PREC']
m.get_inputs1(1)
m.state_read1(1)
