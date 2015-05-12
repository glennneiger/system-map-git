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
distinct_routes_src = os.path.join(env.workspace, 'shp', 'distinct_routes_fall15.shp')
smoothed_routes = os.path.join(env.workspace, 'shp', 'carto_routes.shp')

# intermediate datasets
distinct_routes = os.path.join(temp_shp_dir, 'distinct_routes_temp.shp')
collapsed_routes = os.path.join(temp_shp_dir, 'collapsed_routes.shp')
dissolved_routes = os.path.join(temp_shp_dir, 'dissolved_routes.shp')
simplified_routes = os.path.join(temp_shp_dir, 'simplified_routes.shp')

def getRouteServicePairs():
	"""Get all unique line-service level combinations in the routes feature class"""

	route_service_list = []
	s_fields = ['route_id', 'serv_level']
	with da.SearchCursor(distinct_routes, s_fields) as s_cursor:
		for row in s_cursor:
			if row not in route_service_list:
				route_service_list.append(row)

	return route_service_list

def generateMatchCode():
	"""Generate a code for the collapse dual carriageway tool that will indicate if two
	segments are eligible to be snapped to each other"""

	service_dict = {'frequent': 1, 'standard': 2, 'rush-hour': 3}

	# create a copy of distinct_routes.shp so that the original is not modified
	management.CopyFeatures(distinct_routes_src, distinct_routes)

	merge_field, f_type = 'merge_id', 'LONG'
	management.AddField(distinct_routes, merge_field, f_type)

	u_fields = ['route_id', 'serv_level', merge_field]
	with da.UpdateCursor(distinct_routes, u_fields) as u_cursor:
		for route, service, merge in u_cursor:
			# create a unique id based on frequency and route that is an integer
			merge = int(str(int(route)) + '000' + str(service_dict[service]))
			u_cursor.updateRow((route, service, merge))

def mergeDualCarriageways():
	"""Collapse dual carriageways and turning circles in single, striagt-line roadways, the 
	tools that achieve these effects are run on each route separately then the routes are 
	added back to a single feature class as this yields better results"""

	generateMatchCode()

	# create at feature class to store all of the outputs
	geom_type = 'POLYLINE'
	template = distinct_routes_src
	oregon_spn = arcpy.SpatialReference(2913)
	management.CreateFeatureclass(os.path.dirname(collapsed_routes),
		os.path.basename(collapsed_routes), geom_type, template, 
		spatial_reference=oregon_spn)

	# make a feature layer of the source routes so that selections can be made on it
	distinct_rte_lyr = 'distinct_transit_routes'
	management.MakeFeatureLayer(distinct_routes, distinct_rte_lyr)

	route_service_list = getRouteServicePairs()
	temp_merge = os.path.join(env.workspace, 'shp', 'temp', 'temp_merge.shp')
	temp_collapse = os.path.join(env.workspace, 'shp', 'temp', 'temp_collapse.shp')
	
	route_fields = ['Shape@', 'route_id', 'serv_level', 'route_type']
	i_cursor = da.InsertCursor(collapsed_routes, route_fields)

	for route, service in route_service_list:
		select_type = 'NEW_SELECTION'
		where_clause = """"route_id" = {0} AND "serv_level" = '{1}'""".format(route, service)
		
		management.SelectLayerByAttribute(distinct_rte_lyr, 
			select_type, where_clause)

		# merge dual carriageways
		merge_field = 'merge_id' # '0' in this field means won't be merged
		merge_distance = 100 # feet
		cartography.MergeDividedRoads(distinct_rte_lyr, 
			merge_field, merge_distance, temp_merge)

		# collapse turing circles
		collapse_distance = 550
		cartography.CollapseRoadDetail(temp_merge, collapse_distance, temp_collapse)

		with da.SearchCursor(temp_collapse, route_fields) as s_cursor:
			for row in s_cursor:
				i_cursor.insertRow(row)

	del i_cursor

	# now merge contiguous line segments with common attributes, now that dual carriage-
	# ways have been collapsed the data can be reduced to fewer segments
	dissolve_fields = ['route_id', 'serv_level', 'route_type']
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
	smooth_tolerance = 500
	cartography.SmoothLine(dissolved_routes, 
		smoothed_routes, smooth_algorithm, smooth_tolerance)

	# Note: I experimented with the simplify line tool as well, but it generally made the data
	# less visually pleasing rather than more

mergeDualCarriageways()
smoothRoutes()