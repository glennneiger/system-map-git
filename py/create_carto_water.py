# Grant Humphries, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

# Am scripting this simple process mostly just so that I have record of the
# setting used in the simplify tool

import os
import arcpy
from arcpy import env
from arcpy import cartography
from arcpy import analysis

# Configure environment settings

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
sm_shapefiles = os.path.join(env.workspace, 'shp', 'system_map')
rlis_dir = '//gisstore/gis/Rlis'

rlis_rivers = os.path.join(rlis_dir, 'WATER', 'riv_fill.shp')
carto_rivers = os.path.join(env.workspace, 'shp', 'temp', 'carto_rivers.shp')

def simplifyRivers():
	"""This step isn't mandatory as I believe the buffering step will simplify
	the data to some extent, but the minimum area option removes water bodies
	that are too small to display at the sytsem map level"""

	algorithm = 'POINT_REMOVE' # other option 'BEND_SIMPLIFY'
	tolerance = '25 FEET'
	minimum_area = '200000' # default units are sq ft
	error_option = 'RESOLVE_ERRORS'
	cartography.SimplifyPolygon(rlis_rivers, carto_rivers, 
		algorithm, tolerance, minimum_area, error_option)

def multiBufferRivers():
	"""Create multiple inner buffers of the rlis waterways which when styled
	will simulate the appearance of depth"""

	# generate a list of buffer distance based on the space between buffers
	# and the number of intervals desired
	distance = 45
	intervals = 11

	# this initial value is to create a replica of the orginal geometry as a part
	# of the set, the tool doesn't accept zero as a distance value
	buff_distances = [0.01]
	cur_dist = 0
	while intervals > 1:
		cur_dist -= distance
		buff_distances.append(cur_dist)
		intervals -= 1

	multibuff_rivers = os.path.join(sm_shapefiles, 'multibuffer_rivers.shp')
	buffer_unit = 'FEET'
	analysis.MultipleRingBuffer(carto_rivers, 
		multibuff_rivers, buff_distances, buffer_unit)

simplifyRivers()
multiBufferRivers()