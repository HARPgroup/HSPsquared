import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd


# model class reader
# get model class  to guess object type in this lib 
# the parent object must be known
def model_class_loader(model_name, model_props, container = False):
    # todo: check first to see if the model_name is an attribute on the container
    # Use: if hasattr(container, model_name):
    # if so, we set the value on the container, if not, we create a new subcomp on the container 
    if model_props == None:
        return False
    if type(model_props) is str:
        if is_float_digit(model_props):
            model_object = ModelConstant(model_name, container, float(model_props) )
            return model_object
        else:
            return False
    elif type(model_props) is dict:
      object_class = model_props.get('object_class')
      if object_class == None:
          # return as this is likely an attribute that is used for the containing class as attribute 
          # and is handled by the container 
          # todo: we may want to handle this here?  Or should this be a method on the class?
          # Use: if hasattr(container, model_name):
          return False
      model_object = False
      # Note: this routine uses the ".get()" method of the dict class type 
      #       for attributes to pass in. 
      #       ".get()" will return NoValue if it does not exist or the value. 
      if object_class == 'Equation':
          eqn = model_props.get('equation')
          if type(eqn) is str:
              eqn_str = eqn
          else:
              eqn_str = eqn.get('value')
          model_object = Equation(model_props.get('name'), container, eqn_str )
          #remove_used_keys(model_props, 
      elif object_class == 'Constant':
          model_object = ModelConstant(model_props.get('name'), container, model_props.get('value') )
      elif object_class == 'DataMatrix':
          # add a matrix with the data, then add a matrix accessor for each required variable 
          model_object = ModelObject(model_props.get('name'), container)
          # the matrix accessor should share the state_ix of the base object to set its value
          # and a matrix doesn't actually set its value at each time step, letting the defaul 
          # accessor do the work 
          # but the ops for the matrix maybe should include it's accessor?
      elif object_class == 'ModelLinkage':
          right_path = ''
          link_type = False
          left_path = False
          if 'right_path' in model_props.keys():
            right_path = model_props['right_path']
          if 'link_type' in model_props.keys():
            link_type = model_props['link_type']
          if 'left_path' in model_props.keys():
            left_path = model_props['left_path']
          model_object = ModelLinkage(model_props.get('name'), container, right_path, link_type, left_path)
      else:
          model_object = ModelObject(model_props.get('name'), container)
    # one way to insure no class attributes get parsed as sub-comps is:
    # model_object.remove_used_keys() 
    # better yet to just NOT send those attributes as typed object_class arrays, instead just name : value
    return model_object

def model_class_translate(model_props, object_class):
    # make adjustments to non-standard items 
    # this might better be moved to methods on the class handlers
    if object_class == 'hydroImpoundment':
        # special handling of matrix/storage_stage_area column
        # we need to test to see if the storage table has been renamed 
        # make table from matrix or storage_stage_area
        # then make accessors from 
        storage_stage_area = model_props.get('storage_stage_area')
        matrix = model_props.get('matrix')
        if ( (storage_stage_area == None) and (matrix != None)): 
            model_props['storage_stage_area'] = matrix
            del model_props['matrix']

def model_loader_recursive(model_data, container, loaded_model_objects):
    k_list = model_data.keys()
    object_names = dict.fromkeys(k_list , 1)
    if type(object_names) is not dict:
        return False 
    for object_name in object_names:
        print("Handling", object_name)
        if object_name in {'name', 'object_class', 'id', 'value', 'default'}:
            continue
        model_props = model_data[object_name]
        if type(model_props) is not dict:
            # this is a constant, the loader  is built to handle this, but this causes errors with 
            # properties on the class that are expected so we just skip and trust that all constants
            # are formally declared as type Constant
            continue
        if type(model_props) is dict:
            if not ('object_class' in model_props):
                # this is either a class attribute or an un-handleable meta-data 
                # if the class atttribute exists, we should pass it to container to load 
                print("Skipping un-typed", object_name)
                continue
            print("Translating", object_name)
            # this is a kludge, but can be important 
            object_class = model_props['object_class']
            model_class_translate(model_props, object_class)
        # now we either have a constant (key and value), or a 
        # fully defined object.  Either one should work OK.
        print("Trying to load", object_name)
        model_object = model_class_loader(object_name, model_props, container)
        if model_object == False:
            print("Could not load", object_name)
            continue # not handled, but for now we will continue, tho later we should bail?
        elif not (model_object.state_path in loaded_model_objects.keys()):
            loaded_model_objects[model_object.state_path] = model_object 
        # now for container type objects, go through its properties and handle
        if type(model_props) is dict:
            model_loader_recursive(model_props, model_object, loaded_model_objects)


def model_tokenizer_recursive(model_object, loaded_model_objects):
    k_list = model_object.inputs.keys()
    input_names = dict.fromkeys(k_list , 1)
    if type(input_names) is not dict:
        return False 
    for input_name in input_names:
        print("Checking input", input_name)
        input_path = model_object.inputs[input_name]
        if input_path in loaded_model_objects.keys():
            input_object = loaded_model_objects[input_path]
            model_tokenizer_recursive(input_object, loaded_model_objects)
        else:
            print("Problem loading input", input_name, "input_path", input_path, "not in loaded_model_objects.keys()")
            return False
    # now after tokenizing all inputs this should be OK to tokenize
    model_object.add_op_tokens()

# the implementationsrc_json_node
src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
ssa_el_pid = 4723116 # storage_stage_area did not load, what gives?  Use this to find out
el_pid = 4723109
json_url = src_json_node + "/" + str(el_pid)

# authentication using rest un and pw
jfile = open("/var/www/python/auth.private")
jj = json.load(jfile)
rest_uname = jj[0]['rest_uname']
rest_pass = jj[0]['rest_pw']
basic = HTTPBasicAuth(rest_uname, rest_pass )


# Opening JSON file
jraw =  requests.get(json_url, auth=basic)
model_json = jraw.content.decode('utf-8')
# returns JSON object as Dict
model_data = json.loads(model_json)

qtest = model_data['Q80'] # an example, equation "Q80" 
# check class:
# model_data['object_class']
# 'hydroImpoundment'

# algorithm:
# 1. get a new model class with model_class_loader 
# 2. loop thru children, call recursively to load children models 

# when we find a variable that parses and finds all it's inputs, we return
# note: there should be an array of "inputs" or linked objects, maybe 
# we should prioritize that?
# can we do this economically? Proposed methods:
# 1. while iterate thru obj_queue and parse - tjere are two types of inputs
#       explicit inputs: explicitly provided data path input links or child containment links 
#       implicit inputs: equations and others assume all names are OK and add as inputs 
#                        these must be evaluated after adding all object contained objects first 
#                        since a given path can refer to either the contained context, or the sibling context
#   - create a queue of loaded and unloaded
#     loaded_model_objects = {}
#     container = False 
#     def model_loader_recursive(model_data, container, loaded_model_objects):
#     model_list = model_data.keys()
#     model_queue = dict.fromkeys(model_data , 0)
#   - load object: model_class_loader
#   - check for existence of loaded_model_objects[model_object.state_path]
#     - if it already exists, return 
#   - iterate through sub-components: call model_class_loader 
#     - if is an input (explicit input), try to load the local, if it is a remote one, just load with trust 
#   - when object is finished getting children, call add_op_tokens() method 
#     - the add_op_tokens() method calls find_var_path() for all implicit inputs
#     - the find_var_path() method first looks at local inputs, then siblings, then asks the parent, then tries to match root paths
#     - If a requested path does not have actual entries in state, it will fail
#   - add it to a cache for object that were fully loaded, 
#       - in case they are someone elses inputs no need to redundantly load and loop endlessly
#     loaded_model_objects[model_object.state_path] = model_object 
#   - remove this object from the queue 
# 2. load all, then check inputs:
#   - iterate thru queue: while len(model_queue) > 0: 
#     - load object  
#     - do not load inputs
#     - add sub-components to the top of the queue if they are not in there already:
#       if not (model_object.state_path in list(model_queue.keys())):
#           new_queue = { model_object.state_path: model_object.ix }
#           new_queue.update(model_queue) # this puts the new one in front 
#           model_queue = new_queue_item 
#        **by doing this do we NOT have to call this method recursively ?
#   - iterate thru queue again, check model inputs (trust = False) -- any missing?
#     - yes. message and bail
#     - No. Awesome. We are ready. Run add_op_tokens() method 
# the most important thing is to be able to get 

# testing 
op_tokens, state_paths, state_ix, dict_ix, ts_ix = init_sim_dicts()
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)

k_list = model_data.keys()
obj_queue = dict.fromkeys(k_list , 1)
loaded_model_objects = {}
container = False 
# call it!
model_loader_recursive(model_data, container, loaded_model_objects)
 
# components tests
chez = model_data['0. Impoundment - Lake Chesdin']
discharge = model_data['0. Impoundment - Lake Chesdin']['discharge']
m_class = model_class_loader(chez['name'], chez, container = False)
d_class = model_class_loader(discharge['name'], discharge, m_class)
    
    
# a json NHD from R parser
jfile = open("C:/usr/local/home/git/vahydro/R/modeling/nhd/nhd_simple_8566737.json")
model_data = json.load(jfile)
# returns JSON object as Dict
# get the drainage area as 'area_sqmi'
# Add the Runit equation = Qin / area_sqmi (only valid for a headwater until we get DSN 10 going )
# iterate through nhd tribs and add them together into a big old equation 
loaded_model_objects = {}
container = False 
op_tokens, state_paths, state_ix, dict_ix, ts_ix = init_sim_dicts()
hydr_ix = hydr_get_ix(state_ix, state_paths, domain)
ModelObject.op_tokens, ModelObject.state_paths, ModelObject.state_ix, ModelObject.dict_ix = (op_tokens, state_paths, state_ix, dict_ix)
# call it!
model_loader_recursive(model_data, container, loaded_model_objects)
model_root_object = loaded_model_objects["/STATE/RCHRES_R001"]
model_tokenizer_recursive(model_root_object, loaded_model_objects)
op_tokens[state_paths['/STATE/RCHRES_R001/IVOLin']]
# do 1 test model iteration
test_model(op_tokens, state_ix, dict_ix, ts_ix, 1)
# check values.
# IVOLin should be zero since we are not running inside of HYDR
state_ix[state_paths['/STATE/RCHRES_R001/IVOLin']]
# but this should be non-zero.
state_ix[state_paths['/STATE/RCHRES_R001/trib_area_sqmi']]
# now set a value for IVOL
state_ix[state_paths['/STATE/RCHRES_R001/HYDR/IVOL']] = 100.0
# iterate
test_model(op_tokens, state_ix, dict_ix, ts_ix, 1)
state_ix[state_paths['/STATE/RCHRES_R001/Runit']]
# 1.0076598
state_ix[state_paths["/STATE/RCHRES_R001/Q_nhd_8566763"]]

state_ix[state_paths['/STATE/RCHRES_R001/Qtrib']]
state_ix[state_paths['/STATE/RCHRES_R001/Qup']]
# seems that Qtrib lags execution. It is the 6th element in the queue, which makes sense.
# if this is the driver, then it should be updated the 2nd time through.
# maybe try adding this to the end in the R script?

# debug trib_area_sqmi
# is part of equation ops bad or missing?
obj = loaded_model_objects['/STATE/RCHRES_R001/trib_area_sqmi']
ops = op_tokens[obj.ix]
# op 0 is type (1 = equation), op 1 = ix, op 2 = # of operands triplets
# experiment with adding 2, 3, 4, 5 of the 15 ops and when we reach a failure, eval = 0.0, we have found the bad op  
nops = 16
ops_test = ops[0:nops * 3 + 3]
ops_test[2] = int((len(ops_test) - 3)/3)
exec_eqn(ops_test, state_ix)



# debug Qtrib
# is part of equation ops bad or missing?
obj = loaded_model_objects['/STATE/RCHRES_R001/Qtrib']
ops = op_tokens[obj.ix]
# op 0 is type (1 = equation), op 1 = ix, op 2 = # of operands triplets
# experiment with adding 2, 3, 4, 5 of the 15 ops and when we reach a failure, eval = 0.0, we have found the bad op  
nops = 15
ops_test = ops[0:nops * 3 + 3]
ops_test[2] = int((len(ops_test) - 3)/3)
exec_eqn(ops_test, state_ix)

# now set a new value for IVOL
state_ix[state_paths['/STATE/RCHRES_R001/HYDR/IVOL']] = 60.0
test_model(op_tokens, state_ix, dict_ix, ts_ix, 1)
