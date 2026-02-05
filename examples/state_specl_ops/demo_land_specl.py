# Must be run from the HSPsquared source directory, the h5 file has already been setup with hsp import_uci test10.uci
# bare bones tester - must be run from the HSPsquared source directory
from hsp2.hsp2tools import *
from hsp2.hsp2tools.readUCI import *
from hsp2.hsp2io.hdf import *
from hsp2.hsp2io.io import *


ucifile = "aopN51730.uci"
h5file = "aopN51730.h5"
# try also:
#ucifile="snip.uci" # for a tiny if-else

#readUCI(ucifile, h5file)

# # f.close()
hdf5_instance = HDF5(h5file)

io_manager = IOManager(hdf5_instance)
uci_obj = io_manager.read_parameters()
