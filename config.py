"""
NOSEpick - Nearly Optimal Subsurface Extractor
created by: Brandon S. Tober and Michael S. Christoffersen
date: 25JUN19
last updated: 13JUL2020
environment requirements in nose_env.yml
"""

### USER SPECIFIED VARS ###

# input data path
in_path = "/media/btober/beefmaster/MARS/targ/supl/UAF/2019/hdf5"        

# input basemap path
map_path = "/home/btober/Documents/OIB-AK_qgis/"

# output picks path
out_path = in_path[:-4] + "picks"

# relative permittivity (dielectric constant)
eps_r = 3.15

# param bool amp_out: export pick amplitudes, default False
amp_out = True