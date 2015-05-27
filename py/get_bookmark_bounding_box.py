# (c) Grant Humphries for TriMet, 2015
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
sm_shapefiles = os.path.join(env.workspace, 'shp', 'system_map')
cc_shapefiles = os.path.join(env.workspace, 'shp', 'city_center')

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


def createBoundingBoxPolygon(mxd_path, bkmk_name, out_fc):
	"""Create a polygon that from the coordinates of a bookmark bounding box"""

	geom_type = 'POLYGON'
	oregon_spn = arcpy.SpatialReference(2913)
	management.CreateFeatureclass(os.path.dirname(out_fc),
		os.path.basename(out_fc), geom_type, spatial_reference=oregon_spn)

	name_field, f_type = 'name', 'TEXT'
	management.AddField(out_fc, name_field, f_type)

	# drop defualt field
	drop_field = 'Id'
	management.DeleteField(out_fc, drop_field)

	i_fields = ['Shape@', name_field]
	i_cursor = da.InsertCursor(out_fc, i_fields)

	mxd = mapping.MapDocument(mxd_path)
	for bkmk in arcpy.mapping.ListBookmarks(mxd, bkmk_name):
		extent = bkmk.extent
		pt_array = arcpy.Array()

		pt_array.add(arcpy.Point(extent.XMin, extent.YMin))
		pt_array.add(arcpy.Point(extent.XMin, extent.YMax))
		pt_array.add(arcpy.Point(extent.XMax, extent.YMax))
		pt_array.add(arcpy.Point(extent.XMax, extent.YMin))
		# add first point again to close polygon
		pt_array.add(arcpy.Point(extent.XMin, extent.YMin))

		i_cursor.insertRow((arcpy.Polygon(pt_array), bkmk.name))

	del i_cursor

# city_center_bkmk = 'city center extent'
# city_center_mxd = os.path.join(env.workspace, 'mxd', 'city_center_2015.mxd')
#getBookmarkBbox(city_center_mxd, city_center_bkmk)

# system_map_bkmk = '*system map extent*'
# system_map_mxd = os.path.join(env.workspace, 'mxd', 'system_map_2015.mxd')
# system_map_bbox = os.path.join(sm_shapefiles, 'system_map_bbox.shp')
# createBoundingBoxPolygon(system_map_mxd, system_map_bkmk, system_map_bbox)

city_center_bkmk = '*city center extent*'
city_center_mxd = os.path.join(env.workspace, 'mxd', 'city_center_2015.mxd')
city_center_bbox = os.path.join(cc_shapefiles, 'city_center_bbox.shp')
createBoundingBoxPolygon(city_center_mxd, city_center_bkmk, city_center_bbox)