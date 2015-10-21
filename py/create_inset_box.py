# g. humphries
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import re
import arcpy
from arcpy import da
from arcpy import env
from arcpy import mapping
from arcpy import management

# Configure environment settings
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'

city_center_bkmk = 'city center extent'
city_center_mxd = os.path.join(env.workspace, 'mxd', 'city_center_2015.mxd')
inset_box = os.path.join(env.workspace, 'shp', 'system_map', 'inset_box.shp')

def getBookmarkBbox(mxd_path, bkmk_name):
	"""Get the coordinates of the city center map's bounding box"""

	bkmk_dict = {}
	mxd = mapping.MapDocument(mxd_path)
	for bkmk in arcpy.mapping.ListBookmarks(mxd, bkmk_name):
		bkmk_dict['x-min'] = bkmk.extent.XMin
		bkmk_dict['y-min'] = bkmk.extent.YMin
		bkmk_dict['x-max'] = bkmk.extent.XMax
		bkmk_dict['y-max'] = bkmk.extent.YMax

	return bkmk_dict

def createInsetBox():
	"""The bus mall inset covers a portion of the city center map so that
	needs to be reflected in the inset box, using the inflection point and the
	city center bound box create an fc that contains the inset box"""
	
	inflect_pt = {'x': 7649075, 'y': 686384}
	bkmk_dict = getBookmarkBbox(city_center_mxd, city_center_bkmk)

	geom_type = 'POLYGON'
	oregon_spn = arcpy.SpatialReference(2913)
	management.CreateFeatureclass(os.path.dirname(inset_box), 
		os.path.basename(inset_box), geom_type, spatial_reference=oregon_spn)

	f_name, f_type = 'name', 'TEXT'
	management.AddField(inset_box, f_name, f_type)

	drop_field = 'Id'
	arcpy.management.DeleteField(inset_box, drop_field)

	i_fields = ['Shape@', f_name]
	i_cursor = da.InsertCursor(inset_box, i_fields)

	ap_array = arcpy.Array()
	ap_array.add(arcpy.Point(bkmk_dict['x-min'], bkmk_dict['y-min']))
	ap_array.add(arcpy.Point(bkmk_dict['x-min'], bkmk_dict['y-max']))
	ap_array.add(arcpy.Point(bkmk_dict['x-max'], bkmk_dict['y-max']))
	ap_array.add(arcpy.Point(bkmk_dict['x-max'], inflect_pt['y']))
	ap_array.add(arcpy.Point(inflect_pt['x'], inflect_pt['y']))
	ap_array.add(arcpy.Point(inflect_pt['x'], bkmk_dict['y-min']))
	# add first point again to close polygon
	ap_array.add(arcpy.Point(bkmk_dict['x-min'], bkmk_dict['y-min']))

	i_cursor.insertRow((arcpy.Polygon(ap_array), 'Portland City Center'))

	del i_cursor

createInsetBox()