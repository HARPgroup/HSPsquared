# a model can be created and have its props set manually if desired
# m3 = ModelRCHRES()
# but a Handler class is much better as it can automate everything including QA checks and type formatting
props = {'path':'/RCHRESR001', 'ROVOL':43.1, 'RO':12.75, 'nexits':1 }
m3 = ModelRCHRES()
hm3 = HandlerRCHRES(props)
hm3.set_props(m3)
hm3.init_nexits(m3)
steps = 300000 
# now set this manually for any tests
state_ix[1] = 7.5
state_paths['/RCHRESR001/IVOL'] = 7.5
state_paths['/RCHRESR001/O1'] = 0.0
# load ts with dummy values
for i in ['IVOL', 'POTEV', 'PREC', 'CONVF', 'volumeFT', 'depthFT', 'sareaFT']:
    ts[i] = zeros(steps)

# Create a run list
rchres_list = [ m3 ]
obj_ist = numba.typed.List(rchres_list )
# Set the state info
for i in range(len(obj_ist)):
    obj_ist[i].state_paths = state_paths
    obj_ist[i].state_ix = state_ix 
    obj_ist[i].ts = ts
    # prepare the model for having all configuration
    hm3.prep_run(m3)

