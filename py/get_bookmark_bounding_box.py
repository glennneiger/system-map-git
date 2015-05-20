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

city_center_bkmk = 'city center extent'
city_center_mxd = os.path.join(env.workspace, 'mxd', 'city_center_2015.mxd')

def getBookmarkBbox(mxd_path, bkmk_name):
	"""Create a polygon from based on the city center bookmark and add it to
	a feature class"""

	mxd = mapping.MapDocument(mxd_path)
	for bkmk in arcpy.mapping.ListBookmarks(mxd, bkmk_name):
		print '--------------------------'
		print 'Bounding box for bookmark: {0}'.format(bkmk_name)
		print 'X-min: {0}'.format(bkmk.extent.XMin)
		print 'Y-min: {0}'.format(bkmk.extent.YMin)
		print 'X-max: {0}'.format(bkmk.extent.XMax)
		print 'Y-max: {0}'.format(bkmk.extent.YMax)
		print '--------------------------'

getBookmarkBbox(city_center_mxd, city_center_bkmk)