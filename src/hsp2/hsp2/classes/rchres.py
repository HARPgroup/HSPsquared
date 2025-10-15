from hsp2.hsp2.classes.rchres.handler import HandlerRCHRES

# Define the spec for the ModelRCHRES class
# note: we store the float, int, array props on the HandlerRCHRES object for convenience
#       but we could just as easily opt to keep it in a separate location loaded via include
model_rchres_spec = (model_base + model_make_spec(HandlerRCHRES.float_props, float64) + 
    model_make_spec(HandlerRCHRES.farray_props, float64[:]) + 
    model_make_spec(HandlerRCHRES.carray_props, types.unicode_type) + 
    model_make_spec(HandlerRCHRES.int_props, int32)
)

@jitclass(model_rchres_spec )
class ModelRCHRES:
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
        return
    
    def step(self, step):
        self.state_read(step)
        self.step_HYDR(step)
        #self.step_RQUAL(step)
        #self.step_SEDTRN(step)
        #self.state_write(step)
    
    # state_read_vars: must declare class props that are mutable in state 
    # state_write_vars: all props to expose for reading
    def state_read(self, step):
        # If a particular variable should be shared, but *not* mutable 
        #     it would NOT be in state_read_vars but would be in state_write_vars
        # maybe all of these initial setups should be in a get_inputs() method
        # and then later here in state_read() (or get_state()) we could copy them back?
        self.potev = self.POTEV[step]
        self.prec = self.PREC[step]
        self.convf = self.CONVF[step]
        self.outdgt[:] = self.OUTDGT[step, :]
        # now, the state implementation calls for us to 
        # 1. first set state to IVOL from ts
        # 2. step_state() (for overwrites)
        # 3. Read from state
        self.ivol = self.state_paths[self.path + '/IVOL']
        for i in range(self.nexits):
            self.outdgt[i] = self.state_paths[self.path + '/O' + str(i + 1)]
        #print("state_read outdgt", self.outdgt[i])
        return
    
    def state_read_arr(self, step):
        for n in ['POTEV', 'PREC', 'IVOL', 'ROVOL']:
           self.st[n] = self.state_paths[self.path + str(n + 1)]
        for i in range(self.nexits):
            self.outdgt[i] = self.state_paths[self.path + '/O' + str(i + 1)]
        #print("state_read outdgt", self.outdgt[i])
        return
    
    def state_write_arr(self, step):
        for n in ['POTEV', 'PREC', 'IVOL', 'ROVOL']:
           self.state_paths[self.path + str(n + 1)] = self.st[n] 
        for i in range(self.nexits):
            self.outdgt[i] = self.state_paths[self.path + '/O' + str(i + 1)]
        #print("state_read outdgt", self.outdgt[i])
        return
    
    def state_write(self, step):
        # this happens at the end of each time step after the step() routine is finished
        # If we preload everytihng into its own linked property to ts, we can just write it like so:
        self.PRSUPY[step] = self.prsupy
        self.PRSUPY[step] = self.prsupy
        # OR we go object props are all scalar array keyed items, and we can just copy like names to state
        state_write_vars = ['AVDEP', 'AVVEL', 'DEP', 'HRAD', 'IRRDEM', 'LEN', 'LKFG', 'PRSUPY', 'RO', 'ROVOL', 'SAREA', 'STCOR', 'TAU', 'TWID', 'USTAR', 'VOL', 'VOLEV']
        for i in state_write_vars:
            # TODO: make this do something 
            self.ts[i][step] = self.state[i]
            pass
        return 
    
    def step_HYDR(self, step):
        # options for modes right now (not selectable ATM)
        self.step_HYDRix(step)
        #self.step_HYDRstate(self, step)
        return
    
    def step_SEDTRN(self, step):
        # options for modes right now (not selectable ATM)
        return
    
    def step_HYDR(self, step):
        # self.state_paths[self.path,'/IVOL']
        self.ovol[0] = self.ivol + self.ROVOL
        # versus alternate call external jitted function
        #self.ovol[0] = calc_ovol_blah_blah_blah(self, step)
        return
    
    def step_RQUAL(self, step):
        return

@njit
def fn_hydr_step(rchres, step):
    # will need to pass in dt and get all others from the object state memory
    rchres.ovol[0] = rchres.state_ix[ix] * rchres.ROVOL / rchres.RO


# May be a method of the reach, but with many support functions to reduce size
@njit(cache=True)
def step_hydr(rchres, state, ts, step):
    # MAIN loop Initialization

    # numba limitation, ts can't have both 1-d and 2-d arrays in save Dict
    O      = zeros((steps, nexits))
    OVOL   = zeros((steps, nexits))

    ts['RO']     = RO     = zeros(steps)
    ts['ROVOL']  = ROVOL  = zeros(steps)
    ts['VOL']    = VOL    = zeros(steps)
    ts['VOLEV']  = VOLEV  = zeros(steps)
    ts['IRRDEM'] = IRRDEM = zeros(steps)

    #######################################################################################
    # ******** BEGIN INITIALIZATION BEFORE FIRST RUN STEP ******************
    #######################################################################################
    zeroindex = fndrow(0.0, rchres.volumeFT)                                           #$1126-1127
    topvolume = rchres.volumeFT[-1]

    vol = ui['VOL'] * rchres.VFACT   # hydr-init, initial volume of water
    if vol >= topvolume:
        errors[1] += 1      # ERRMSG1: extrapolation of rchtab will take place
    
    # find row index that brackets the VOL
    indx = fndrow(vol, rchres.volumeFT)
    if rchres.nodfv:  # simple interpolation, the hard way!!
        v1 = rchres.volumeFT[indx]
        v2 = rchres.volumeFT[indx+1]
        rod1,od1[:] = demand(v1, rowsFT[indx,  :], funct, rchres.nexits, rchres.delts, rchres.convf, colind, rchres.outdgt)
        rod2,od2[:] = demand(v2, rowsFT[indx+1,:], funct, rchres.nexits, rchres.delts, rchres.convf, colind, rchres.outdgt)
        a1 = (v2 - vol) / (v2 - v1)
        o[:] = a1 * od1[:] + (1.0 - a1) * od2[:]
        ro   = (a1 * rod1) + ((1.0 - a1) * rod2)
    else:
        ro,o[:] = demand(vol, rowsFT[indx,:], funct, rchres.nexits, rchres.delts, rchres.convf, colind, rchres.outdgt)  #$1159-1160

    # back to PHYDR
    if rchres.AUX1FG >= 1:
        dep, stage, sarea, avdep, twid, hrad = auxil(rchres.volumeFT, rchres.depthFT, rchres.sareaFT, indx, vol, rchres.length, rchres.STCOR, rchres.AUX1FG, errors) # initial

    # hydr-irrig
    irexit = int(ui['IREXIT']) -1    # irexit - exit number for irrigation withdrawals, 0 based ???
    #if irexit >= 1:
    irminv = ui['IRMINV']
    rirwdl = 0.0
    #rirdem = 0.0
    #rirsht = 0.0
    irrdem = 0.0

    # store initial outflow from reach:
    ui['ROS'] = ro
    for index in range(rchres.nexits):
        ui['OS' + str(index + 1)] = o[index]

    # other initial vars
    rchres.rovol = 0.0
    volev = 0.0
    IVOL0   = model.IVOL                   # the actual inflow in simulation native units\
    #######################################################################################
    # ******** END INITIALIZATION BEFORE FIRST RUN STEP ******************
    #######################################################################################


    #######################################################################################
    # the following section (2 of 3) added by rb to HYDR, this one to prepare for dynamic state including special actions
    #######################################################################################
    hydr_ix = hydr_get_ix(state_ix, state_paths, state_info['domain'])
    # these are integer placeholders faster than calling the array look each timestep
    o1_ix, o2_ix, o3_ix, ivol_ix = hydr_ix['O1'], hydr_ix['O2'], hydr_ix['O3'], hydr_ix['IVOL']
    ro_ix, rovol_ix, volev_ix, vol_ix = hydr_ix['RO'], hydr_ix['ROVOL'], hydr_ix['VOLEV'], hydr_ix['VOL']
    # handle varying length rchres.outdgt
    out_ix = arange(rchres.nexits)
    if rchres.nexits > 0:
        out_ix[0] = o1_ix
    if rchres.nexits > 1:
        out_ix[1] = o2_ix
    if rchres.nexits > 2:
        out_ix[2] = o3_ix
    #######################################################################################
    
    # HYDR (except where noted)
    colind[:] = COLIND[step, :]
    roseff = ro
    rchres.oseff[:] = rchres.o[:]

    #######################################################################################
    # the following section (3 of 3) added by rb to accommodate dynamic code, operations models, and special actions
    #######################################################################################
    # set state_ix with value of local state variables and/or needed vars
    # Note: we pass IVOL0, not IVOL here since IVOL has been converted to different units
    state_ix[ro_ix], state_ix[rovol_ix] = ro, rchres.rovol
    di = 0
    for oi in range(rchres.nexits):
        state_ix[out_ix[oi]] = rchres.outdgt[oi] 
    state_ix[vol_ix], state_ix[ivol_ix] = vol, IVOL0[step]
    state_ix[volev_ix] = volev
    # - these if statements may be irrelevant if default functions simply return
    #   when no objects are defined.
    if (state_info['state_step_om'] == 'enabled'):
        pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)
    if (state_info['state_step_hydr'] == 'enabled'):
        state_step_hydr(state_info, state_paths, state_ix, dict_ix, ts_ix, hydr_ix, step)
    if (state_info['state_step_om'] == 'enabled'):
        #print("trying to execute state_step_om()")
        # model_exec_list contains the model exec list in dependency order
        # now these are all executed at once, but we need to make them only for domain end points
        step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, step)   # traditional 'ACTIONS' done in here
    if ( (state_info['state_step_hydr'] == 'enabled')
        or (state_info['state_step_om'] == 'enabled') ):
        # Do write-backs for editable STATE variables
        # OUTDGT is writeable
        for oi in range(rchres.nexits):
            rchres.outdgt[oi] = state_ix[out_ix[oi]]
        # IVOL is writeable.
        # Note: we must convert IVOL to the units expected in _hydr_
        # maybe routines should do this, and this is not needed (but pass rchres.VFACT in state)
        rchres.ivol = state_ix[ivol_ix] * rchres.VFACT
    # End dynamic code step()
    #######################################################################################

    # vols, sas variables and their initializations  not needed.
    if irexit >= 0:             # irrigation exit is set, zero based number
        if rirwdl > 0.0:  # equivalent to OVOL for the irrigation exit
            vol = irminv if irminv > vol - rirwdl else vol - rirwdl
            if vol >= rchres.volumeFT[-1]:
                errors[1] += 1 # ERRMSG1: extrapolation of rchtab will take place

            # DISCH with hydrologic routing
            indx = fndrow(vol, rchres.volumeFT)                 # find row index that brackets the VOL
            vv1 = rchres.volumeFT[indx]
            rod1,od1[:] = demand(vv1, rowsFT[indx,  :], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)
            vv2 = rchres.volumeFT[indx+1]
            rod2,od2[:] = demand(vv2, rowsFT[indx+1,:], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)
            aa1 = (vv2 - vol) / (vv2 - vv1)
            ro   = (aa1 * rod1)    + ((1.0 - aa1) * rod2)
            o[:] = (aa1 * od1[:])  + ((1.0 - aa1) * od2[:])

            # back to HYDR
            if rchres.AUX1FG >= 1:     # recompute surface area and depth
                dep, stage, sarea, avdep, twid, hrad = auxil(rchres.volumeFT, rchres.depthFT, rchres.sareaFT, indx, vol, rchres.length, rchres.STCOR,
                                                                rchres.AUX1FG, errors)
        else:
            irrdem =  0.0
        #rchres.o[irexit] = 0.0                                                   #???? not used anywhere, check if rchres.o[irexit]

    rchres.prsupy = rchres.prec * sarea
    if rchres.uunits == 2:
        rchres.prsupy = rchres.prec * sarea / 3.281
    volt   = vol + rchres.ivol + rchres.prsupy
    volev = 0.0
    if rchres.AUX1FG:                  # subtract evaporation 
        volpev = rchres.POTEV[step] * sarea
        if rchres.uunits == 2:
            volpev = rchres.POTEV[step] * sarea / 3.281
        if volev >= volt:
            volev = volt
            volt = 0.0
        else:
            volev = volpev
            volt -= volev

    # ROUTE/NOROUT  calls
    # common code
    volint = volt - (rchres.KS * roseff * rchres.delts)    # find intercept of eq 4 on vol axis
    if volint < (volt * 1.0e-5):
        volint = 0.0
    if volint <= 0.0:  #  case 3 -- no solution to simultaneous equations
        indx  = zeroindex
        vol   = 0.0
        ro    = 0.0
        rchres.o[:]  = 0.0
        rchres.rovol = volt

        if roseff > 0.0: # numba limitation, cant combine into one line
            rchres.ovol[:] = (rchres.rovol/roseff) * rchres.oseff[:]
        else:
            rchres.ovol[:] = rchres.rovol / rchres.nexits

    else:   # case 1 or 2
        oint = volint * facta1      # == ointsp, so ointsp variable dropped
        if rchres.nodfv:
            # ROUTE
            rodz,rchres.odz[:] = demand(0.0, rowsFT[zeroindex,:], funct, rchres.nexits, rchres.delts, convf, colind,  rchres.outdgt)
            if oint > rodz:
                # SOLVE - case 1-- outflow demands can be met in full
                # premov will be used to check whether we are in a trap, arbitrary value
                premov = -20
                move   = 10

                vv1 = rchres.volumeFT[indx]
                rod1,od1[:] = demand(vv1, rowsFT[indx, :], funct, rchres.nexits, rchres.delts, convf,colind, rchres.outdgt)
                vv2 = rchres.volumeFT[indx+1]
                rod2,od2[:] = demand(vv2, rowsFT[indx+1,:], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)

                while move != 0:
                    facta2 = rod1 - rod2
                    factb2 = vv2 - vv1
                    factc2 = vv2 * rod1 - vv1 * rod2
                    det = facta1 * factb2 - facta2
                    if det <= 0.0:
                        det = 0.0001
                        errors[0] += 1  # ERRMSG0: SOLVE is indeterminate

                    vol = max(0.0, (oint * factb2 - factc2 ) / det)
                    if vol > vv2:
                        if indx >= rchres.nrows-2:
                            if vol > topvolume:
                                errors[1] += 1 # ERRMSG1: extrapolation of rchtab will take place
                            move = 0
                        else:
                            move   = 1
                            indx  += 1
                            vv1    = vv2
                            od1[:] = od2[:]
                            rod1   = rod2
                            vv2    = rchres.volumeFT[indx+1]
                            rod2,od2[:] = demand(vv2, rowsFT[indx+1,:], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)
                    elif vol < vv1:
                        indx  -= 1
                        move   = -1
                        vv2    = vv1
                        od2[:] = od1[:]
                        rod2   = rod1
                        vv1    = rchres.volumeFT[indx]
                        rod1,od1[:] = demand(vv1, rowsFT[indx,:], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)
                    else:
                        move = 0

                    # check whether algorithm is in a trap, yo-yoing back and forth
                    if move + premov == 0:
                        errors[2] += 1      # ERRMSG2: oscillating trap
                        move = 0
                    premov = move

                ro = oint - facta1 * vol
                if  vol < 1.0e-5:
                    ro  = oint
                    vol = 0.0
                if ro < 1.0e-10:
                    ro  = 0.0
                if ro <= 0.0:
                    rchres.o[:] = 0.0
                else:
                    diff  = vol - vv1
                    factr = 0.0 if diff < 0.01 else  diff / (vv2 - vv1)
                    rchres.o[:]  = od1[:] + (od2[:] - od1[:]) * factr
            else:
                # case 2 -- outflow demands cannot be met in full
                ro  = 0.0
                for i in range(rchres.nexits):
                    tro  = ro + rchres.odz[i]
                    if tro <= oint:
                        rchres.o[i] = rchres.odz[i]
                        ro = tro
                    else:
                        rchres.o[i] = oint - ro
                        ro = oint
                vol = 0.0
                indx = zeroindex
        else:
            # NOROUT
            rod1,od1[:] = demand(vol, rowsFT[indx,:], funct, rchres.nexits, rchres.delts, convf, colind, rchres.outdgt)
            if oint >= rod1: #case 1 -outflow demands are met in full
                ro   = rod1
                vol  = volint - rchres.coks * ro * rchres.delts
                if vol < 1.0e-5:
                    vol = 0.0
                rchres.o[:] = od1[:]
            else:    # case 2 -outflow demands cannot be met in full
                ro  = 0.0
                for i in range(rchres.nexits):
                    tro  = ro + rchres.odz[i]
                    if tro <= oint:
                        rchres.o[i] = rchres.odz[i]
                        ro = tro
                    else:
                        rchres.o[i] = oint - ro
                        ro = oint
                vol = 0.0
                indx = zeroindex

        # common  ROUTE/NOROUT code
        #  an irrigation demand was made before routing
        if  (irexit >= 0) and (irrdem > 0.0):    #  an irrigation demand was made before routing
            rchres.oseff[irexit] = irrdem
            rchres.o[irexit]     = irrdem
            roseff       += irrdem
            ro           += irrdem
            IRRDEM[step] = irrdem

        # estimate the volumes of outflow
        rchres.ovol[:] = (rchres.KS * rchres.oseff[:] + rchres.coks * rchres.o[:]) * rchres.delts
        rchres.rovol   = (rchres.KS * roseff   + rchres.coks * ro)   * rchres.delts

    # HYDR
    if rchres.nexits > 1:
        O[step,:]    = rchres.o[:]    * rchres.SFACTA * rchres.LFACTA
        OVOL[step,:] = rchres.ovol[:] / rchres.VFACT
    RO[step]     = ro     * rchres.SFACTA * rchres.LFACTA
    ROVOL[step]  = rchres.rovol  / rchres.VFACT
    VOLEV[step]  = volev  / rchres.VFACT
    VOL[step]    = vol    / rchres.VFACT

    if rchres.AUX1FG:   # compute final depth, surface area
        if vol >= topvolume:
            errors[1] += 1       # ERRMSG1: extrapolation of rchtab
        indx = fndrow(vol, rchres.volumeFT)
        dep, stage, sarea, avdep, twid, hrad = auxil(rchres.volumeFT, rchres.depthFT, rchres.sareaFT, indx, vol, rchres.length, rchres.STCOR, rchres.AUX1FG, errors)
        DEP[step]   = dep
        SAREA[step] = sarea / rchres.AFACT

        if vol > 0.0 and sarea > 0.0:
            twid  = sarea / rchres.length
            avdep = vol / sarea
        elif rchres.AUX1FG == 2:
            twid = sarea / rchres.length
            avdep = 0.0
        else:
            twid = 0.0
            avdep = 0.0

        if rchres.AUX2FG:
            avvel = (rchres.length * ro / vol) if vol > 0.0 else 0.0
        if rchres.AUX3FG:
            if avdep > 0.0:
                # SHEAR; ustar (bed shear velocity), tau (bed shear stress)
                if rchres.LKFG:              # flag, 1:lake, 0:stream
                    ustar = avvel / (17.66 + (log10(avdep / (96.5 * rchres.db50u))) * 2.3 / rchres.AKAPPA)
                    tau   =  rchres.GAM/rchres.GRAV * ustar**2              #3796
                else:
                    hrad = (avdep*twid)/(2.0*avdep + twid) # hydraulic radius, manual eq 41
                    slope = rchres.DELTH / rchres.length
                    ustar = sqrt(rchres.GRAV * slope * hrad)
                    tau = (rchres.GAM * slope) * hrad
            else:
                ustar = 0.0
                tau   = 0.0
                hrad  = 0.0
            USTAR[step] = ustar * rchres.LFACTA
            TAU[step]   = tau   * rchres.TFACTA

        AVDEP[step] = avdep
        AVVEL[step] = avvel
        HRAD[step]  = hrad
        TWID[step]  = twid
    # END MAIN LOOP

    return errors

# THIS IS THE END OF THE HYDR LOOP, NOT YET IMPLEMENTED
def hydr_finish(rchres):
    # NUMBA limitation for ts, and saving to HDF5 file is in individual columns
    if rchres.nexits > 1:
        for i in range(rchres.nexits):
            rchres.ts[Olabels[i]]    = rchres.O[:,i]
            rchres.ts[OVOLlabels[i]] = rchres.OVOL[:,i]