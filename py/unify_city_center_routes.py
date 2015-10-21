# g. humphries
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from arcpy import da
from arcpy import env
from arcpy import management

# Set project directories
project_dir = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
temp_dir = os.path.join(project_dir, 'shp', 'temp')
cc_shapefiles = os.path.join(project_dir, 'shp', 'city_center')
sm_shapefiles = os.path.join(project_dir, 'shp', 'system_map')

# Configure environment settings
env.overwriteOutput = True
env.workspace = os.path.join(project_dir, 'system-map-git', 'city_center_carto_routes.gdb')

def createCcBusLabelsFc():
	"""The offset routes for the city center have only one set of geometries for
	each service level, but there needs to be labels for each line so generate a 
	unique geometry for each of the routes the line segments represent"""

	geom_type = 'POLYLINE'
	template = os.path.join(sm_shapefiles, 'distinct_routes.shp')
	oregon_spn = arcpy.SpatialReference(2913)
	bus_labels_cc = os.path.join(cc_shapefiles, 'bus_labels_cc.shp')
	management.CreateFeatureclass(os.path.dirname(bus_labels_cc), 
		os.path.basename(bus_labels_cc), geom_type, template, 
		spatial_reference=oregon_spn)

	i_fields = ['Shape@', 'route_id', 'serv_level', 'route_type']
	i_cursor = da.InsertCursor(bus_labels_cc, i_fields)

	s_fields = i_fields[:]
	s_fields[1] = 'routes'
	for fc in arcpy.ListFeatureClasses():
		if 'bus' in fc:
			with da.SearchCursor(fc, s_fields) as cursor:
				routes_ix = cursor.fields.index('routes')
				for row in cursor:
					for route in row[routes_ix].split(','):
						new_row = list(row)
						new_row[routes_ix] = route

						i_cursor.insertRow((new_row))

	del i_cursor

def assignRouteNumbersToRail(fc, name_field, num_field):
	"""Some fc's only have routes as names, they need to have the route number and
	this function provides that based on the route name"""

	rail_num_dict = {
		'ns': 193, 'cl': 194, 'ns/cl': '193,194',
		'r': 90, 'b': 100, 'y': 190, 'g': 200, 'o': 290
	}

	with da.UpdateCursor(fc, [name_field, num_field]) as cursor:
		for name, num in cursor:
			l_name = name.lower()
			if l_name in rail_num_dict:
				num = str(rail_num_dict[l_name])
			else:
				num_list = []
				for l in l_name:
					num_list.append(rail_num_dict[l])

				num = ','.join([str(r) for r in num_list])

			cursor.updateRow((name, num))

def generateCcCombinedRoutesFc():
	"""The city center routes are split into a few feature classes for the various
	modes of transportation, combine them into a unified one"""

	geom_type = 'POLYLINE'
	template = os.path.join(env.workspace, 'frequent_bus_carto')
	oregon_spn = arcpy.SpatialReference(2913)
	combined_routes_cc = os.path.join(cc_shapefiles, 'combined_routes_cc.shp')
	management.CreateFeatureclass(os.path.dirname(combined_routes_cc), 
		os.path.basename(combined_routes_cc), geom_type, template, 
		spatial_reference=oregon_spn)

	name_field = 'LINE'
	route_fields = ['Shape@', 'routes', 'serv_level', 'route_type']
	i_cursor = da.InsertCursor(combined_routes_cc, route_fields)

	for fc in arcpy.ListFeatureClasses(feature_type='Polyline'):
		if name_field in [f.name for f in arcpy.ListFields(fc)]:
			assignRouteNumbersToRail(fc, name_field, route_fields[1])

		with da.SearchCursor(fc, route_fields) as cursor:
			for row in cursor:
				i_cursor.insertRow(row)

	del i_cursor

createCcBusLabelsFc()
generateCcCombinedRoutesFc()