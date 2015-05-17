# (c) Grant Humphries for TriMet, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from arcpy import env
from arcpy import edit

# Configure environment settings
project_dir = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
env.workspace = os.path.join(project_dir, 'system-map-git', 'carto_routes.gdb')

def curvesToVertices():
	"""Some GIS application can't read bezier curves which I used heavily in the 
	creation of the cartographic reprsentation of the transit routes, this function
	replaces the curves with discrete vertices"""

	feat_datasets = ['frequent', 'standard', 'rush_hour', 'rail_tram']
	for fd in feat_datasets:
		# the gdb must be set to env.workspace for listfeature classes to work
		for fc in arcpy.ListFeatureClasses(feature_dataset=fd):
			fc_path = os.path.join(env.workspace, fd, fc)
			densification_method = 'OFFSET'
			tolerance = 1 # foot
			edit.Densify(fc_path, densification_method, max_deviation=tolerance)

curvesToVertices()