"""
This is a alpha concept.  Maybe it is wrong to assemble networks here like this
And should instead use R or VAHydro to pass these networks in as json?
"""
from HSP2.om_model_object import ModelObject
from HSP2.om_model_object import ModelLinkage
from HSP2.utilities_specl import *
from numba import njit
class MicroWatershedModel(ModelObject):
    def __init__(self, name, container = False):
        super(ModelObject, self).__init__(name, container, model_props = [])
        self.optype = 9 # 0 - shell object, 1 - equation, 2 - datamatrix, 3 - input, 4 - broadcastChannel, 5 - SimTimer, 6 - Conditional, 7 - ModelConstant (numeric), 8 - matrix accessor, 9 - MicroWatershedModel, 10 - MicroWatershedNetwork
        # add relevant component equations and broadcasts etc.
        self.init_components(model_props)
    
    def init_components(self, model_props = []):
        # listen to children
        broadcast_params = [["Qtrib","Qtrib"],["trib_area_sqmi","trib_area_sqmi"]]
        listen_tribs = ModelBroadcast("Listen_to_Children", self, 'read', 'hydroObject', 'child', broadcast_params)
        # Qlocal and Qin: note: Runit will come from parent
        # this type of trib assumes that it is atomic, that is, the local_area_sqmi does not change
        # and therefore, local area cannot be decreased by new tribs being created and 
        drainage_area_sqmi = self.handle_prop(model_props, "drainage_area_sqkm")
        # qwe assume this is an equation.
        # this is not a great construct, perhaps we should not use?
        drainage_area_sqmi = Equation('drainage_area_sqmi', self, drainage_area_sqmi)
        # full resegmentation
        Qlocal = Equation('Qlocal', self, "Runit * local_area_sqmi")
        drainage_area_sqmi = Equation('drainage_area_sqmi', self, "trib_area_sqmi + local_area_sqmi")
        Qin = Equation('Qin', river, "Qlocal + Qtrib")
        # Qout 
        Qout = Equation('Qout', river, "Qout * 1.0") # add * 1.0 becuz single arg eqn is broke
        # Vout 
        # Storage 
        # Send to Parent (trib_area_sqmi, Qtrib, wd_upstream_mgd, ps_upstream_mgd)
        broadcast_params = [["Qout","Qtrib"],["drainage_area_sqmi","trib_area_sqmi"]]
        SendToParent = ModelBroadcast("Send_to_Parent", self, 'send', 'hydroObject', 'parent', broadcast_params)
        # Read from Children (trib_area_sqmi, Qtrib, wd_upstream_mgd, ps_upstream_mgd)
    
    def tokenize(self):
        # call parent method to set basic ops common to all 
        super().tokenize()
    
    def add_op_tokens(self):
        # this puts the tokens into the global simulation queue 
        # can be customized by subclasses to add multiple lines if needed.
        super().add_op_tokens()

# njit functions for runtime

@njit
def pre_step_micro_network(op, state_ix, dict_ix):
    # this is unnecessary 
    result = False
    return result

