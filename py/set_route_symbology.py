# (c) Grant Humphries for TriMet, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import re
import arcpy
from arcpy import env
from arcpy import mapping
from arcpy import management

# Configure environment settings
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
mxd_path = os.path.join(env.workspace, 'mxd', 'system_map_2015.mxd')

mxd = mapping.MapDocument(mxd_path)
symbology = os.path.join(env.workspace, 'shp', 'system_map_route_symbology.lyr')

def applySymbologyToRoutes():
	""""""

	for lyr in mapping.ListLayers(mxd):
		if 'Carto Routes' in lyr.longName and lyr.isFeatureLayer:
			print lyr.name
			management.ApplySymbologyFromLayer(lyr, symbology)
			#lyr.save()
	mxd.save()


applySymbologyToRoutes()
