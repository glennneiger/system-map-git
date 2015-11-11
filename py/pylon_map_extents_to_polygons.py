# Grant Humphries, 2015
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from os import path
from arcpy import da
from arcpy import env
from arcpy import mapping
from arcpy import management

# Configure environment settings

# Allow shapefiles to be overwritten and set the current workspace
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'

mxd_path = path.join(env.workspace, 'mxd', 'new_pylon_maps.mxd')
mxd = mapping.MapDocument(mxd_path)
data_pages = mxd.dataDrivenPages
data_frame = data_pages.dataFrame

pylon_extents = path.join(env.workspace, 'shp', 'pylon', 'new_pylon_map_extents.shp')
name_field = 'name'

def createExtentFeatureClass():
	"""Create a feature class to the hold the map extent geometries"""

	geom_type = 'POLYGON'
	oregon_spn = arcpy.SpatialReference(2913)
	
	management.CreateFeatureclass(path.dirname(pylon_extents), 
		path.basename(pylon_extents), geom_type, spatial_reference=oregon_spn)

	f_type = 'TEXT'
	management.AddField(pylon_extents, name_field, f_type)

	drop_field = 'Id'
	management.DeleteField(pylon_extents, drop_field)

def getDataPagesMapExtents():
	"""Get the exent of each of the maps in the data driven pages collection
	and write them as polygons to a feature class"""
	
	createExtentFeatureClass()

	i_fields = ['Shape@', name_field]
	i_cursor = da.InsertCursor(pylon_extents, i_fields)

	for page_num in range(1, data_pages.pageCount + 1):
		data_pages.currentPageID = page_num
		extent = data_frame.extent
		pt_array = arcpy.Array()
		
		pt_array.add(arcpy.Point(extent.XMin, extent.YMin))
		pt_array.add(arcpy.Point(extent.XMin, extent.YMax))
		pt_array.add(arcpy.Point(extent.XMax, extent.YMax))
		pt_array.add(arcpy.Point(extent.XMax, extent.YMin))
		# add first point again to close polygon
		pt_array.add(arcpy.Point(extent.XMin, extent.YMin))

		# get the page name of the map and add it as an attribute
		pg_name_field = data_pages.pageNameField.name
		page_name = data_pages.pageRow.getValue(pg_name_field)
		
		i_cursor.insertRow((arcpy.Polygon(pt_array), page_name))

	del i_cursor

getDataPagesMapExtents()