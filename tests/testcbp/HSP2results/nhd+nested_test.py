# Set up model by loading:
# tests/testcbp/HSP2results/load_test_riverseg.py
# - creates object "root", which contains all simulation data beneath it
#   - insures that timer elements get executed
# load NHD subsheds from file
#jfile = open("C:/Workspace/tmp/8567221.json") # has 3 elements 
#jfile = open("C:/Workspace/tmp/8566791.json") # has only 1 element 
jfile = open("C:/Workspace/tmp/8566731.json") # has only 2 elements 
model_data = json.load(jfile)
# in future, we may load the whole dang model, but for now 
# this json file has only the trib info 
trib_data = model_data['RCHRES_R001']
model_loader_recursive(trib_data, river)

# load a single object to observe:
# obj = model_object_cache['/STATE/RCHRES_R001/nhd_8566731']
# obj_data = model_data['RCHRES_R001']['nhd_8566731']['read_from_children']
# obj_data = model_data['RCHRES_R001']['nhd_8566731']['send_to_parent']
# rfc = model_class_loader('send_to_children', obj_data, obj)
# rfc.

print("Loaded the following objects/paths:", state_paths)
print("Insuring all paths are valid, and connecting models as inputs")
# now load 
model_path_loader(model_object_cache)
model_root = model_object_cache[river.state_path]
# create ordered list and tokenize
model_exec_list = [] # the order list of execution
model_touch_list = [] # a holder for objects that have been already traced but may not have been added yet (prevents endless recursion)
model_tokenizer_recursive(timer, model_object_cache, model_exec_list, model_touch_list)
model_tokenizer_recursive(model_root, model_object_cache, model_exec_list, model_touch_list)
model_exec_list = np.asarray(model_exec_list, dtype="i8")
ModelObject.model_exec_list = model_exec_list

# run the model 
#steps = 3
#iterate_models(op_tokens, state_ix, dict_ix, ts_ix, steps)
set_state(state_ix, state_paths, '/STATE/RCHRES_R001/HYDR/IVOL', 44.3)
pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 1)
step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 1)
set_state(state_ix, state_paths, '/STATE/RCHRES_R001/HYDR/IVOL', 15.7)
pre_step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 2)
step_model(model_exec_list, op_tokens, state_ix, dict_ix, ts_ix, 2)

# can look at all kinds of state variables like this:
# get this variables state 
# since we know this must have a trib:
moc = model_object_cache
trib2 = river.get_object('nhd_8566731')
trib1 = trib2.get_object('nhd_8566705')
trib2.get_state('Runit')
# Another way to get objects 
#trib2.get_object('hydroObject').get_object('Qtrib').inputs
#trib2.get_object('hydroObject').get_object('Qtrib').get_object('Qtrib67').get_exec_order()
trib2.get_state('Runit')

trib2.get_state('Qout')
trib2.get_state('Qin')
trib2.get_state('Qlocal')
trib2.get_state('Qtrib')
trib2.get_state('trib_area_sqmi')
trib2.get_exec_order()
trib2.get_exec_order('Qtrib')
trib2.get_exec_order('Qlocal')
trib2.get_exec_order('Qtrib')
trib2.get_exec_order()
trib1.get_exec_order('Qtrib')
trib1.get_exec_order('Qlocal')
trib1.get_exec_order('Qtrib')
trib1.get_exec_order('Qout')

step_one(trib2.op_tokens, trib2.op_tokens[trib2.ix], trib2.state_ix, trib2.dict_ix, trib2.ts_ix, step)

trsq = model_object_cache[trib2.find_var_path('hydroObject') + "/" + 'trib_area_sqmi']
trsq.get_state()




# if we only know the local short name (like in an equation), we 
# can still find it as the get_state() routine should check through linkages etc to find values
# Ex: get tje trib_area_sqmi value used in the Qlocal equation 
river.get_state('trib_area_sqmi')
# Get Runit from Qlocal equation
river.get_state('Runit')

# 0.4463933228106152
Qlocal.get_state('local_area_sqmi')
# and any object can be used to get the value of any path
Qlocal.get_state('/STATE/RCHRES_R001/local_area_sqmi')
river.get_state('Qtrib')
river.get_state('/STATE/RCHRES_R001/hydroObject/Qtrib')
Trib1.get_state('Qout')

# look at the ops:
Listen_to_Children.linkages
SendToParent.linkages[1].ops
# test the ops
test_model_link(SendToParent.linkages[1].ops, state_ix, ts_ix, 1)
