# g. humphries
# ArcGIS Version:   10.3.0
# Python Version:   2.7.8
#--------------------------------

import os
import arcpy
from arcpy import da
from arcpy import env
from arcpy import analysis
from arcpy import management
from arcpy import cartography

# Set project directories
env.overwriteOutput = True
env.workspace = '//gisstore/gis/PUBLIC/GIS_Projects/System_Map/2015'
sm_shapefiles = os.path.join(env.workspace, 'shp', 'system_map')
rlis_dir = '//gisstore/gis/Rlis'
orca_sites = os.path.join(rlis_dir, 'LAND', 'orca_sites.shp')
simplified_parks = os.path.join(sm_shapefiles, 'simplified_parks.shp')

def simplifyParks():
	"""Simplify parks so that they can effectively be displayed at a scale
	of 1:100,000 on the principal system map"""
	
	# limit parks to sites that are at least 100 acres and that are named
	parks_lyr = 'parks_layer'
	park_type = 'Park and/or Natural Area'
	park_size = 100 # acres
	where_clause = """"TYPE" = '{0}' AND "ACREAGE" > {1} AND "SITENAME" <> ' '"""
	where_populated = where_clause.format(park_type, park_size)
	management.MakeFeatureLayer(orca_sites, parks_lyr, where_populated)

	# use union tool to get rid of any holes in park features
	gaps_setting = 'NO_GAPS'
	parks_union = os.path.join('in_memory', 'parks_union')
	analysis.Union(parks_lyr, parks_union, gaps=gaps_setting)

	# the holes have been filled in by the union tool, but 
	parks_dissolve = os.path.join('in_memory', 'parks_dissolve')
	management.Dissolve(parks_union, parks_dissolve)

	# split mulitpart features to single part
	single_part_parks = os.path.join('in_memory', 'single_part_parks')
	management.MultipartToSinglepart(parks_dissolve, single_part_parks)

	# delete any park fragments
	parks_fields = ['OID@', 'SHAPE@AREA']
	with da.UpdateCursor(single_part_parks, parks_fields) as cursor:
		for oid, area in cursor:
			if area < 1000000: # square feet
				cursor.deleteRow()

	# simplify the parks by smoothing out their edges
	algorithm = 'PAEK'
	tolerance = 5000 # feet
	endpoint_option = 'NO_FIXED'
	cartography.SmoothPolygon(single_part_parks, simplified_parks, 
		algorithm, tolerance, endpoint_option)

simplifyParks()