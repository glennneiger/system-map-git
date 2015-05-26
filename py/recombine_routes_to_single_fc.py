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
project_dir = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
temp_dir = os.path.join(project_dir, 'shp', 'temp')
offset_routes = os.path.join(project_dir, 'shp', 'offset_routes.shp')

# workspace must be set to this gdb for listfeature classes to work
env.workspace = os.path.join(project_dir, 'system-map-git', 'carto_routes.gdb')

def createUnifiedFc():
	"""Create feature class to hold all of the routes that have been offset as
	individual fc's"""

	geom_type = 'POLYLINE'
	template = os.path.join(project_dir, 'shp', 'distinct_routes.shp')
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
			print fc
			fc_path = os.path.join(env.workspace, fd, fc)
			with da.SearchCursor(fc_path, route_fields) as s_cursor:
				for row in s_cursor:
					i_cursor.insertRow(row)

	del i_cursor

def validateGeometry():
	"""Check for geometry errors and multipart features that may have been introduced
	in the manual editing process of creating the offsets"""

	# Check for geometry errors, this tool doesn't flag a lot of the aspects I'm
	# interested in, thus the other steps below
	error_table = os.path.join(temp_dir, 'carto_errors.dbf')
	management.CheckGeometry(offset_routes, error_table)

	# Identify any multipart features
	multipart_dump = os.path.join(temp_dir, 'multipart_dump.shp')
	management.MultipartToSinglepart(offset_routes, multipart_dump)

	multipart_dict = {}
	dump_fields = ['OID@', 'ORIG_FID']
	with da.SearchCursor(multipart_dump, dump_fields) as s_cursor:
		for oid, orig_id in s_cursor:
			if orig_id not in multipart_dict:
				multipart_dict[orig_id] = 1
			else:
				multipart_dict[orig_id] += 1

	print "Features with the following fid's are multipart:"
	for orig_id, count in multipart_dict.iteritems():
		if count > 1:
			print orig_id

	# Find other errors like shared geometries and deadends using the merge divided
	# roads tool, I'm not actually interested in the output of this tool but rather the
	# validation output that it generates
	merge_field, field_type = 'merge_id', 'LONG'
	management.AddField(offset_routes, merge_field, field_type)

	# validation output will be logged here (not that user name portion may be variable):
	# C:\Users\humphrig\AppData\Local\ESRI\Geoprocessing
	merge_distance = 100 # feet
	validation_merge = os.path.join('in_memory', 'validation_merge')
	cartography.MergeDividedRoads(offset_routes, 
		merge_field, merge_distance, validation_merge)

	# drop the merge field as it no longer needed
	management.DeleteField(offset_routes, merge_field)

createUnifiedFc()
populateUnifiedFc()
validateGeometry()