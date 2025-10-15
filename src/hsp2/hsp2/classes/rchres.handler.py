from hsp2.hsp2.classes.base import HandlerBase

class HandlerRCHRES(HandlerBase):
    float_props = ['DB50', 'db50u', 'AUX1FG', 'AUX2FG', 'AUX3FG', 'AVDEP', 'AVVEL', 'DELTH', 'DEP', 'HRAD', 'IRRDEM', 'LEN', 
                   'POTEV', 'PREC', 'IVOL',
                   'potev', 'prec', 'ivol', 'avdep',
                   'LKFG', 'PRSUPY', 'RO', 'ROVOL', 'SAREA', 'LEN', 'length', 'STCOR', 'TAU', 'TWID', 'USTAR', 'VOL', 'VOLEV', 'delts',
                   'VFACT', 'AFACT', 'LFACTA', 'SFACTA', 'TFACTA', 'GAM', 'GRAV', 'length', 'AKAPPA',
                   'volumeFT', 'depthFT', 'sareaFT', 'convf', 'nodfv', 'KS', 'coks', 'facta1']
    int_props = ['nrows', 'nexits', 'AUX1FG', 'AUX2FG', 'AUX3FG', 'LKFG', 'DELTH','uunits']
    farray_props = ['o', 'odz', 'ovol', 'oseff', 'CONVF', 'DEP', 'OUTDGT']
    carray_props = ['state_read_vars', 'state_write_vars']
    # props with number of exits
    nexprops = ['o', 'odz', 'ovol', 'oseff', 'outdgt', 'od1', 'od2', 'colind']
    def __init__(self, model_props = None):
        super(HandlerRCHRES, self).__init__(model_props)
        return
    
    def prep_run(self, model):
        # insure that all local timeseries linkages are correct, inputs are sound
        # later we will test if this is advantageous or if the notation
        # self.inputs['PREC'] will work as well in equations
        model.POTEV = model.ts['POTEV'] / 12.0 # why are these conversion in the HYDR.py _hydr() routine?  Seems like they belong elsewhere
        model.PREC = model.ts['PREC'] / 12.0 # why are these conversion in the HYDR.py _hydr() routine?  Seems like they belong elsewhere
        model.CONVF = model.ts['CONVF']
        model.convf = model.CONVF[0]
        model.volumeFT = model.ts['volumeFT']
        model.depthFT = model.ts['depthFT']
        model.sareaFT = model.ts['sareaFT']
        # units conversion constants, 1 ACRE is 43560 sq ft. assumes input in acre-ft
        model.VFACT = 43560.0
        model.AFACT = 43560.0
        model.LFACTA = 1.0
        model.SFACTA = 1.0
        model.TFACTA = 1.0
        # physical constants (English units)
        model.GAM = 62.4  # density of water
        model.GRAV = 32.2  # gravitational acceleration
        model.length = model.LEN * 5280.0 # length of reach, in feet
        model.AKAPPA = 0.4  # von karmen constant
        model.coks = 1.0 - model.KS
        model.facta1 = 1.0 / (rchres.coks * rchres.delts)
        # is passed in to the _hydr routine as a standalone argument, but it is actually a timeseries
        # The routine hydr() calculates it, and that is not ideal, as it should be parsed earlier, like in this step
        # so, we set the model outdgt as the first time steps value to initialize
        model.outdgt[:] = model.ts['OUTDGT'][0] 
        if model.uunits == 2:
            # si units conversion constants, 1 hectare is 10000 sq m, assumes area input in hectares, vol in Mm3
            model.VFACT = 1.0e6
            model.AFACT = 10000.0
            # physical constants (English units)
            model.GAM = 9806.  # density of water
            model.GRAV = 9.81  # gravitational acceleration
        model.IVOL = model.ts['IVOL']  * model.VFACT # or sum civol, zeros if no inflow ???
        model.CONVF = model.ts['CONVF']
        # try this approach from old version.  We segment the ts df so that our local model variables
        # are references, thus, the updates made to the model property immediately propagate to the 
        # ts - now, this should *really* propagate to the global ts. i.e. ts["TIMESERIES/" + model.path]
        # these next rows are outputs of the model, so they will be calculated
        model.ts['PRSUPY'] = model.PRSUPY = zeros(steps)
        model.ts['RO']     = model.RO     = zeros(steps)
        model.ts['ROVOL']  = model.ROVOL  = zeros(steps)
        model.ts['VOL']    = model.VOL    = zeros(steps)
        model.ts['VOLEV']  = model.VOLEV  = zeros(steps)
        model.ts['IRRDEM'] = model.IRRDEM = zeros(steps)
        model.avdep = 0.0
        if model.AUX1FG:
            model.ts['DEP']   = DEP   = zeros(steps)
            model.ts['SAREA'] = SAREA = zeros(steps)
            model.ts['USTAR'] = USTAR = zeros(steps)
            model.ts['TAU']   = TAU   = zeros(steps)
            model.ts['AVDEP'] = AVDEP = zeros(steps)
            model.ts['AVVEL'] = AVVEL = zeros(steps)
            model.ts['HRAD']  = HRAD  = zeros(steps)
            model.ts['TWID']  = TWID  = zeros(steps)
        
        
        if model.uunits == 2:
            model.db50u = model.DB50 / 40.0 # mean diameter of bed material
        else:
            model.db50u   = model.DB50 / 12.0 # mean diameter of bed material
        
        model.od1    = zeros(model.nexits)
        model.od2    = zeros(model.nexits)
        model.colind = zeros(model.nexits)
        model.colind[:] = model.COLIND[0,:]
        return
    
    def set_props(self, model, strict = False ):
        # sub classes can check to see if this is in the right format, or change to numba compatible types etc.
        super().set_props(model, strict)
        # Handle special props
        if 'delt' in self.model_props:
            model.delts = self.model_props['delt'] * 60.0
    
    def init_nexits(self, model):
        # faster to preallocate arrays - like MATLAB)
        for i in self.nexprops:
            setattr(model, i, zeros(model.nexits))
        return

# extracted from function hsp2.HYDR.hydr() initializes all relevant inputs/extracts from uci 
# NOT YET COMPLETE, JUST A BEGINNING, all initialization steps take place here, one time before
# entering the main model execution loop
# THIS MAY BECOME PART OF THE HandlerRCHRES code as method prep_run()
# - some of this has *already* been added to prep_run()
# or maybe even part of a HandlerRCHRES.init() method to be added above
def init_hydr(rchres, handler, siminfo, uci, ts, ftables, state):
    ''' find the state of the reach/reservoir at the end of the time interval
    and the outflows during the interval

    CALL: hydr(store, general, ui, ts, state)
       store is the Pandas/PyTable open store
       general is a dictionary with simulation level infor (OP_SEQUENCE for example)
       ui is a dictionary with RID specific HSPF UCI like data
       ts is a dictionary with RID specific timeseries
       state is a dictionary that contains all dynamic code dictionaries such as: 
       - specactions is a dictionary with all special actions
    '''
    steps   = siminfo['steps']                # number of simulation points
    rchres.uunits  = siminfo['units']
    rchres.nexits  = int(uci['PARAMETERS']['NEXITS'])

    u = uci['PARAMETERS']
    # This next several lines for funct, ODGTF all appear to act as it there can be several "keys" in PARAMETERS
    # then they add a sub-array containing a slot for each of the nexits
    # however, later when they are used it is clear that the array is 1 dimensional with only nexits slots
    # so it appears that this code enables something that is unsupportable?
    rchres.funct  = array([u[name] for name in u.keys() if name.startswith('FUNCT')]).astype(int)[0:nexits]
    rchres.ODGTF  = array([u[name] for name in u.keys() if name.startswith('ODGTF')]).astype(int)[0:nexits]
    rchres.ODFVF  = array([u[name] for name in u.keys() if name.startswith('ODFVF')]).astype(int)[0:nexits]

    u = uci['STATES']
    rchres.colin = array([u[name] for name in u.keys() if name.startswith('COLIN')]).astype(float)[0:nexits]
    rchres.outdg = array([u[name] for name in u.keys() if name.startswith('OUTDG')]).astype(float)[0:nexits]

    # COLIND timeseries might come in as COLIND, COLIND0, etc. otherwise UCI default
    names = list(sorted([n for n in ts if n.startswith('COLIND')], reverse=True))
    df = DataFrame()
    for i,c in enumerate(ODFVF):
        df[i] = ts[names.pop()][0:steps] if c < 0 else full(steps, c)
    rchres.COLIND = df.to_numpy()

    # OUTDGT timeseries might come in as OUTDGT, OUTDGT0, etc. otherwise UCI default
    names = list(sorted([n for n in ts if n.startswith('OUTDG')], reverse=True))
    df = DataFrame()
    for i,c in enumerate(ODGTF):
        df[i] = ts[names.pop()][0:steps] if c > 0 else zeros(steps)
    rchres.OUTDGT = df.to_numpy()

    # generic SAVE table doesn't know nexits for output flows and rates
    if nexits > 1:
        u = uci['SAVE']
        for key in ('O', 'OVOL'):
            for i in range(nexits):
                u[f'{key}{i+1}'] = u[key]
            del u[key]

    # optional - defined, but can't used accidently
    for name in ('SOLRAD','CLOUD','DEWTEMP','GATMP','WIND'):
        if name not in ts:
            ts[name] = full(steps, nan)

    # optional timeseries
    for name in ('IVOL','POTEV','PREC'):
        if name not in ts:
            ts[name] = zeros(steps)
    ts['CONVF'] = initm(siminfo, uci, 'VCONFG', 'MONTHLY_CONVF', 1.0)

    # extract key columns of specified FTable for faster access (1d vs. 2d)
    rchres.rchtab = ftables[f"{uci['PARAMETERS']['FTBUCI']}"]
    #rchtab = store[f"FTABLES/{uci['PARAMETERS']['FTBUCI']}"]
    ts['volumeFT'] = rchres.rchtab['Volume'].to_numpy() * VFACT
    ts['depthFT']  = rchres.rchtab['Depth'].to_numpy()
    ts['sareaFT']  = rchres.rchtab['Area'].to_numpy()   * AFACT
    rchres.rchtab = rchres.rchtab.to_numpy()
    # we may only need to store the uci as ui on the HandlerRCHRES rather than the 
    # ModelRCHRES runtime object 
    handler.ui = make_numba_dict(uci) # Note: all values coverted to float automatically
    handler.ui['steps']  = steps
    handler.ui['delt']   = siminfo['delt']
    handler.ui['nexits'] = nexits
    handler.ui['errlen'] = len(ERRMSGS)
    handler.ui['nrows']  = rchres.rchtab.shape[0]
    handler.ui['nodfv']  = any(ODFVF)
    handler.ui['uunits'] = uunits

    # Numba can't do 'O' + str(i) stuff yet, so do it here. Also need new style lists
    rchres.Olabels = List()
    rchres.OVOLlabels = List()
    for i in range(rchres.nexits):
        rchres.Olabels.append(f'O{i+1}')
        rchres.OVOLlabels.append(f'OVOL{i+1}')

    #######################################################################################
    # the following section (1 of 3) added to HYDR by rb to handle dynamic code and special actions
    #######################################################################################
    # state_info is some generic things about the simulation
    # must be numba safe, so we don't just pass the whole state which is not
    state_info = Dict.empty(key_type=types.unicode_type, value_type=types.unicode_type)
    state_info['operation'], state_info['segment'], state_info['activity'] = state['operation'], state['segment'], state['activity']
    state_info['domain'], state_info['state_step_hydr'], state_info['state_step_om'] = state['domain'], state['state_step_hydr'], state['state_step_om']
    hsp2_local_py = state['hsp2_local_py']
    # It appears necessary to load this here, instead of from main.py, otherwise,
    # _hydr_() does not recognize the function state_step_hydr()? 
    if (hsp2_local_py != False):
        from hsp2_local_py import state_step_hydr
    else:
        from hsp2.hsp2.state_fn_defaults import state_step_hydr
    # initialize the hydr paths in case they don't already reside here
    hydr_init_ix(state, state['domain'])
    # must split dicts out of state Dict since numba cannot handle mixed-type nested Dicts
    state_ix, dict_ix, ts_ix = state['state_ix'], state['dict_ix'], state['ts_ix']
    state_paths = state['state_paths']
    ep_list = ["DEP","IVOL","O1","O2","O3","OVOL1","OVOL2","OVOL3","PRSUPY","RO","ROVOL","SAREA","TAU","USTAR","VOL","VOLEV"]
    rchres.model_exec_list = model_domain_dependencies(state, state_info['domain'], ep_list)
    rchres.model_exec_list = asarray(model_exec_list, dtype="i8") # format for use in numba
    rchres.op_tokens = state['op_tokens']
    #######################################################################################

    return

hydr_finish(rchres):
    # extracted from function hydr() after execution of full timesteps returned from call to _hydr_()
    if 'O'    in rchres.ts:  del rchres.ts['O']
    if 'OVOL' in rchres.ts:  del rchres.ts['OVOL']

    # save initial outflow(s) from reach:
    rchres.uci['PARAMETERS']['ROS'] = rchres.ui['ROS']
    for i in range(rchres.nexits):
        rchres.uci['PARAMETERS']['OS'+str(i+1)] = rchres.ui['OS'+str(i+1)]
    