# (c) Grant Humphries for TriMet, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from arcpy import da
from arcpy import env
from arcpy import management
from arcpy import cartography

# Configure environment settings

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
temp_shp_dir = os.path.join(env.workspace, 'shp', 'temp')

# final datasets
serv_level_routes_src = os.path.join(env.workspace, 'shp', 'service_level_routes_fall15.shp')
serv_level_routes = os.path.join(temp_shp_dir, 'service_level_routes_temp.shp')

dissolved_routes = os.path.join(temp_shp_dir, 'city_center_dissolved_routes.shp')
smoothed_routes = os.path.join(temp_shp_dir, 'city_center_smoothed_routes.shp')

def getModeServicePairs():
	"""Get all unique line-service level combinations in the routes feature class"""

	mode_service_list = []
	s_fields = ['route_type', 'serv_level']
	with da.SearchCursor(serv_level_routes, s_fields) as s_cursor:
		for row in s_cursor:
			if row not in mode_service_list:
				mode_service_list.append(row)

	return mode_service_list

def generateMatchCode():
	"""Generate a code for the collapse dual carriageway tool that will indicate if two
	segments are eligible to be snapped to each other"""

	service_dict = {'frequent': 1, 'standard': 2, 'rush-hour': 3}

	# create a copy of service_level_routes.shp so that the original is not modified
	management.CopyFeatures(serv_level_routes_src, serv_level_routes)

	merge_field, f_type = 'merge_id', 'LONG'
	management.AddField(serv_level_routes, merge_field, f_type)

	u_fields = ['serv_level', 'route_type',  merge_field]
	with da.UpdateCursor(serv_level_routes, u_fields) as u_cursor:
		for service, r_type, merge in u_cursor:
			# match field must be of type int 
			merge = int(str(service_dict[service]) + str(int(r_type)))
			u_cursor.updateRow((service, r_type, merge))

def mergeDualCarriageways():
	"""Collapse dual carriageways and turning circles in single, striagt-line roadways, the 
	tools that achieve these effects are run on each route separately then the routes are 
	added back to a single feature class as this yields better results"""

	generateMatchCode()

	# create at feature class to store all of the outputs
	geom_type = 'POLYLINE'
	template = serv_level_routes_src
	oregon_spn = arcpy.SpatialReference(2913)
	collapsed_routes = os.path.join(temp_shp_dir, 'collapsed_routes.shp')
	management.CreateFeatureclass(os.path.dirname(collapsed_routes),
		os.path.basename(collapsed_routes), geom_type, template, 
		spatial_reference=oregon_spn)

	# make a feature layer of the source routes so that selections can be made on it
	serv_level_rte_lyr = 'service_level_routes'
	management.MakeFeatureLayer(serv_level_routes, serv_level_rte_lyr)

	mode_service_list = getModeServicePairs()
	temp_merge = os.path.join(env.workspace, 'shp', 'temp', 'temp_merge.shp')
	temp_collapse = os.path.join(env.workspace, 'shp', 'temp', 'temp_collapse.shp')
	
	route_fields = ['Shape@', 'routes', 'serv_level', 'route_type']
	i_cursor = da.InsertCursor(collapsed_routes, route_fields)

	for mode, serv in mode_service_list:
		select_type = 'NEW_SELECTION'
		where_clause = """"route_type" = {0} AND "serv_level" = '{1}'""".format(mode, serv)
		management.SelectLayerByAttribute(serv_level_rte_lyr, 
			select_type, where_clause)

		# merge dual carriageways
		merge_field = 'merge_id' # '0' in this field means won't be merged
		merge_distance = 100 # feet
		cartography.MergeDividedRoads(serv_level_rte_lyr, 
			merge_field, merge_distance, temp_merge)

		# collapse turing circles
		collapse_distance = 100
		cartography.CollapseRoadDetail(temp_merge, collapse_distance, temp_collapse)

		with da.SearchCursor(temp_collapse, route_fields) as s_cursor:
			for row in s_cursor:
				i_cursor.insertRow(row)

	del i_cursor

	# now merge contiguous line segments with common attributes, now that dual carriage-
	# ways have been collapsed the data can be reduced to fewer segments
	dissolve_fields = ['routes', 'serv_level', 'route_type']
	geom_class = 'SINGLE_PART'
	line_handling = 'UNSPLIT_LINES'
	management.Dissolve(collapsed_routes, dissolved_routes, dissolve_fields, 
		multi_part=geom_class, unsplit_lines=line_handling)

def smoothRoutes():
	"""Smooth sharp edges with smooth line tool for more aesthetically pleasing look"""

	# The tolerance of 500 feet here results in a maximum displacement of ~75 ft which
	# is miniamal at teh scale of the system map (but large enough to make things less
	# jagged while retaining most of the detail)
	smooth_algorithm = 'PAEK'
	smooth_tolerance = 250
	cartography.SmoothLine(dissolved_routes, 
		smoothed_routes, smooth_algorithm, smooth_tolerance)

	# Note: I experimented with the simplify line tool as well, but it generally made the data
	# less visually pleasing rather than more

#mergeDualCarriageways()
smoothRoutes()