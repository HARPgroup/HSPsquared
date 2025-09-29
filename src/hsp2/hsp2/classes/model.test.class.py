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
        self.ts_ix = Dict.empty(key_type=types.int64, value_type=types.float64[:])
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
    # *******************************************************************
    # ts_read*() : populate state with timeseries values
    # ts_read*() : are a temporary, all timeseries objects will have a pre_step() function that loads their current
    # *******************************************************************
    # ts 
    def ts_read_path2ix(self, step):
        # reads time series from string keyed array
        self.state_ix[self.potev_ix] = self.ts[self.path + '/POTEV'][step]
        self.state_ix[self.prec_ix] = self.ts[self.path + '/PREC'][step]
    def ts_read_ix2ix(self, step):
        # this is a temporary, all timeseries objects will have a pre_step() function that loads their current
        # reads time series from integer keyed array
        self.state_ix[self.potev_ix] = self.ts_ix[self.potev_ix][step]
        self.state_ix[self.prec_ix] = self.ts_ix[self.prec_ix][step]
    def ts_read_path2path(self, step):
        # reads time series from string keyed array
        for n in ['POTEV', 'PREC']:
            self.state_paths[self.path + "/" + n] = self.ts[self.path + "/" + n][step]
    # get_state* functions loads data from global to local state (essential for code readability)
    def get_state_tspath2prop(self, step):
        # this DOES NOT REQUIRE a ts_read* function, as the input is an actual object
        # value into the state array
        self.potev = self.ts[self.path + '/POTEV'][step]
        self.prec = self.ts[self.path + '/PREC'][step]
    def get_state_tsix2prop(self, step):
        # this DOES NOT REQUIRE a ts_read* function, as the input is an actual object
        # value into the state array
        self.potev = self.ts_ix[self.potev_ix][step]
        self.prec = self.ts_ix[self.prec_ix][step]
    def get_state_ix2arr(self, step):
        # value into the state array
        # dynamically defined links could work this way: arbitrary TS links without code, just local name+ remote IX
        self.st['POTEV'] = self.state_ix[self.potev_ix]
        self.st['PREC'] = self.state_ix[self.prec_ix]
    def get_state_tsix2arr(self, step):
        # this DOES NOT REQUIRE a ts_read* function, as the input is an actual object
        # value into the state array
        # dynamically defined links could work this way: arbitrary TS links without code, just local name+ remote IX
        self.st['POTEV'] = self.ts_ix[self.potev_ix][step]
        self.st['PREC'] = self.ts_ix[self.prec_ix][step]
    def get_state_tspath2arr(self, step):
        # remote path value into the state array
        for n in ['POTEV', 'PREC']:
            self.st[n] = self.state_paths[self.path + "/" + n]
    def get_state_ref2prop(self, step):
        # this DOES NOT REQUIRE a ts_read* function, as the input is an actual object
        # reference from a timeseries dataframe
        self.prec = self.PREC[step]
        self.potev = self.POTEV[step]
    def get_state_ref2arr(self, step):
        # this DOES NOT REQUIRE a ts_read* function, as the input is an actual object
        # reference from a timeseries dataframe
        self.st['PREC'] = self.PREC[step]
        self.st['POTEV'] = self.POTEV[step]
    def get_state_path2arr(self, step):
        # remote path value into the state array
        for n in ['POTEV', 'PREC']:
            self.st[n] = self.state_paths[self.path + "/" + n]
        # value into the state array
        # dynamically defined links could work this way: arbitrary TS links without code, just local name+ remote IX
        self.st['POTEV'] = self.state_ix[self.potev_ix]
        self.st['PREC'] = self.state_ix[self.prec_ix]
    
    def exec_prop(self, step):
        # calculate the values
        result = self.prec - self.potev
        if (result < 0):
            result = 0
        self.ovol = result
    def exec_arr(self, step):
        # calculate the values
        result = self.st['PREC'] - self.st['POTEV']
        if result < 0:
            result = 0
        self.st['OVOL'] = result
    
    def state_write_prop2ix(self, step):
        self.state_ix[self.prec_ix] = self.prec
        self.state_ix[self.potev_ix] = self.potev
        self.state_ix[self.ovol_ix] = self.ovol
        return
    def state_write_prop2path(self, step):
        self.state_paths[self.path + '/' + '/PREC'] = self.prec
        self.state_paths[self.path + '/' + '/POTEV'] = self.potev
        self.state_paths[self.path + '/' + '/OVOL'] = self.ovol
        return
    def state_write_arr2path(self, step):
        for i in ['PREC', 'OVOL', 'POTEV']:
            self.state_paths[self.path + '/' + i] = self.st[i]
        return
    def state_write_arr2ix(self, step):
        self.state_ix[self.prec_ix] = self.st['PREC']
        self.state_ix[self.potev_ix] = self.st['POTEV']
        self.state_ix[self.ovol_ix] = self.st['OVOL']
        return
    
    def step1(self, step):
        self.get_state_ref2prop(step)
        self.exec_prop(step)
        if ( (step/10000) == round(step/10000)):
            print("Rain - PET = OVOL", self.prec, self.potev, self.ovol)
            print("State = ", self.state_ix)
        self.state_write_prop2ix(step)
        return
    # test with reference TS inputs, and local associative array as state storage
    def step2(self, step):
        self.get_state_ref2arr(step)
        self.exec_arr(step)
        if ( (step/10000) == round(step/10000)):
            print("Rain - PET = OVOL", self.st['PREC'], self.st['POTEV'], self.st['OVOL'])
            print("State = ", self.state_ix)
        self.state_write_arr2ix(step)
    # reads ts path to state_ix, then state_ix to prop
    def step3(self, step):
        self.ts_read_path2ix(step)
        self.get_state_tsix2prop(step)
        self.exec_prop(step)
        if ( (step/10000) == round(step/10000)):
            print("Rain - PET = OVOL", self.prec, self.potev, self.ovol)
            print("State = ", self.state_ix)
        self.state_write_prop2ix(step)
    
    def get_inputs2(self, step):
        # this is a temporary, all timeseries objects will have a pre_step() function that loads their current
        # value into the state array
        self.potev = self.POTEV[step]
        self.prec = self.PREC[step]
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
def iteration_test1(it_ops, it_nums):
    ctr = 0
    for n in range(it_nums):
        for i in range(len(it_ops)):
            it_ops[i].step1(n)
        ctr=ctr+1
    print("Completed ", ctr, " loops")


@njit
def iteration_test2(it_ops, it_nums):
    ctr = 0
    for n in range(it_nums):
        for i in range(len(it_ops)):
            it_ops[i].step2(n)
        ctr=ctr+1
    print("Completed ", ctr, " loops")


@njit
def iteration_test3(it_ops, it_nums):
    ctr = 0
    for n in range(it_nums):
        for i in range(len(it_ops)):
            it_ops[i].step3(n)
        ctr=ctr+1
    print("Completed ", ctr, " loops")

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
ts_ix = m.ts_ix
state_ix = m.state_ix
state_paths = m.state_paths
ts['/RCHRESR001/PREC'] = prec
ts['/RCHRESR001/POTEV'] = potev
ts_ix[m.prec_ix] = prec
ts_ix[m.potev_ix] = potev
m.ts = ts 
m.ts_ix = ts_ix 

m.POTEV = ts['/RCHRESR001/POTEV']
m.PREC = ts['/RCHRESR001/PREC']
#m.get_inputs1(1)
#m.state_read1(1)

# now do a full test
obj_ist = numba.typed.List([m] )
starttime = time.time();iteration_test1(obj_ist, steps );endtime = time.time()
print("Elapsed time:", (endtime - starttime))
print("Rain - PET = OVOL", m.prec, m.potev, m.ovol)

