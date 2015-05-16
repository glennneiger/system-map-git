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
project_dir = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
offset_routes = os.path.join(project_dir, 'shp', 'offset_routes.shp')

# workspace must be set to this gdb for listfeature classes to work
env.workspace = os.path.join(project_dir, 'shp', 'indiv_carto_routes.gdb')

def createUnifiedFc():
	"""Create feature class to hold all of the routes that have been offset as
	individual fc's"""

	geom_type = 'POLYLINE'
	template = os.path.join(project_dir, 'shp', 'carto_routes.shp')
	oregon_spn = arcpy.SpatialReference(2913)
	management.CreateFeatureclass(os.path.dirname(offset_routes),
		os.path.basename(offset_routes), geom_type, template,
		spatial_reference=oregon_spn)

def populateUnifiedFc():
	"""Iterate through all of the individual route feature classes and add them
	to common fc"""

	route_fields = ['Shape@', 'route_id', 'serv_level', 'route_type']
	i_cursor = da.InsertCursor(offset_routes, route_fields)

	feat_datasets = ['frequent', 'standard', 'rush_hour', 'rail_tram']
	for fd in feat_datasets:
		for fc in arcpy.ListFeatureClasses(feature_dataset=fd):
			# exclude these as a different more generalized fc is being used
			# to represent the streetcar
			if fc not in ('ns_standard_carto', 'cl_standard_carto'):
				print fc
				fc_path = os.path.join(env.workspace, fd, fc)
				with da.SearchCursor(fc_path, route_fields) as s_cursor:
					for row in s_cursor:
						i_cursor.insertRow(row)

	del i_cursor

createUnifiedFc()
populateUnifiedFc()