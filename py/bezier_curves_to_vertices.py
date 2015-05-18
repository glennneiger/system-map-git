# (c) Grant Humphries for TriMet, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import re
import arcpy
from arcpy import env
from arcpy import edit

# Configure environment settings
project_dir = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
env.workspace = os.path.join(project_dir, 'system-map-git', 'carto_routes.gdb')

# routes should be referenced by three digit numbers like '004', '075', '115', etc.
# for MAX use 'max', WES - 'wes', Streetcar - 'streetcar', Aerial Tram - 'aerial'
route_list = [
	'006',
	'wes',
	'max',
	'streetcar',
	'aerial',
	'015',
	'075',
	'115'
]

def curvesToVertices(route_list=None):
	"""Some GIS application can't read bezier curves which I used heavily in the 
	creation of the cartographic reprsentation of the transit routes, this function
	replaces the curves with discrete vertices"""

	feat_datasets = ['frequent', 'standard', 'rush_hour', 'rail_tram']
	for fd in feat_datasets:
		# the gdb must be set to env.workspace for listfeature classes to work
		for fc in arcpy.ListFeatureClasses(feature_dataset=fd):
			flag = True

			if route_list:
				num_test = re.match('^line_([0-9]{3})_.+', fc)
				if num_test:
					route_id = num_test.group(1)
				else:
					route_id = re.match('([a-z]+)_.+', fc).group(1)

				if route_id not in route_list:
					flag = False

			if flag:
				fc_path = os.path.join(env.workspace, fd, fc)
				densification_method = 'OFFSET'
				tolerance = 1 # foot
				edit.Densify(fc_path, densification_method, max_deviation=tolerance)

#curvesToVertices(route_list)