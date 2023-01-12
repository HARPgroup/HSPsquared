import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd


# model class reader
# get model class  to guess object type in this lib 
# the parent object must be known
def model_class_loader(model_name, model_props, container = False):
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
          return False
      model_object = False
      # Note: this routine uses the ".get()" method of the dict class type 
      #       for attributes to pass in. 
      #       ".get()" will return NoValue if it does not exist or the value. 
      if object_class == 'Equation':
          eqn = model_props.get('equation')
          model_object = Equation(model_props.get('name'), container, eqn )
          #remove_used_keys(model_props, 
      elif object_class == 'Constant':
          model_object = Constant(model_props.get('name'), container, model_props.get('value') )
      else:
          model_object = ModelObject(model_props.get('name'), container)
    # one way to insure no class attributes get parsed as sub-comps is:
    # model_object.remove_used_keys() 
    # better yet to just NOT send those attributes as typed object_class arrays, instead just name : value
    return model_object


def model_loader_recursive(model_data, container, loaded_model_objects):
    k_list = model_data.keys()
    object_names = dict.fromkeys(k_list , 1)
    if type(object_names) is not dict:
        return False 
    for object_name in object_names:
        if object_name in {'name', 'object_class', 'id', 'value', 'default'}:
            continue
        model_props = model_data[object_name]
        if type(model_props) is dict:
            if not ('object_class' in model_props):
                print("Skipping un-typed", object_name)
                continue
            print("Trying to load", object_name)
            model_object = model_class_loader(object_name, model_props, container)
            if model_object == False:
                print("Could not load", object_name)
                continue # not handled, but for now we will continue, tho later we should bail?
            elif not (model_object.state_path in loaded_model_objects.keys()):
                loaded_model_objects[model_object.state_path] = model_object 
                if type(model_props) is dict:
                    model_loader_recursive(model_props, model_object, loaded_model_objects)

# the implementationsrc_json_node
src_json_node = 'http://deq1.bse.vt.edu/d.dh/node/62'
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


    