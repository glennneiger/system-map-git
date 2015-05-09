# (c) Grant Humphries for TriMet, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from arcpy import da
from arcpy import env
from arcpy import management

# Configure environment settings

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'

all_routes = os.path.join(env.workspace, 'shp', 'distinct_routes.shp')
route_gdb = os.path.join(env.workspace, 'shp', 'indiv_carto_routes.gdb')
route_fields = ['Shape@', 'route_id', 'serv_level', 'route_type']

def separateRoutes():
	""""""
	type_dict = {
		1: 'bus', 
		2: 'aerial tram', 
		3: 'wes', 
		4: 'streetcar', 
		5: 'max'
	}
	
	line_dict = {
		193: 'ns', 
		194: 'cl', 
		208: 'aerial_tram'
		# 999 is a place holder being used since the route_id field is type: int
		# and doesn't accept characters other than numbers
		999: 'new_sellwood_99' 
	}

	management.CreateFileGDB(os.path.dirname(route_gdb), os.path.basename(route_gdb))

	service_list = []
	service_levels = []

	with da.SearchCursor(all_routes, route_fields[1:]) as s_cursor:
		for rte, serv, r_type in s_cursor:
			rs = (int(rte), serv)
			if r_type not in (3, 5) and rs not in service_list:
				service_list.append(rs)

			if serv not in service_levels:
				service_levels.append(serv)

	for level in service_levels:
		management.CreateFeatureDataset(route_gdb, level.replace('-', '_'))

	for route_id, service in service_list:
		# translate number to name for streetcar and aerial tram lines
		try:
			route_text = line_dict[route_id]
		except:
			route_text = 'line_{0}'.format(route_id)
		
		service_text = service.replace('-', '_')
		route_name = '{0}_{1}_carto'.format(route_text, service_text)
		
		current_route = os.path.join(route_gdb, service_text, route_name)
		geom_type = 'POLYLINE'
		template = all_routes
		oregon_spn = arcpy.SpatialReference(2913)
		management.CreateFeatureclass(os.path.dirname(current_route), 
			os.path.basename(current_route), geom_type, template, 
			spatial_reference=oregon_spn)

		i_cursor = da.InsertCursor(current_route, route_fields)

		with da.SearchCursor(all_routes, route_fields) as s_cursor:
			for geom, rte, serv, r_type in s_cursor: 
				if rte == route_id and serv == service:
					i_cursor.insertRow((geom, rte, serv, r_type))

		del i_cursor

separateRoutes()