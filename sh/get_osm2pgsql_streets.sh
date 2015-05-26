# !/bin/sh

pg_user=geoserve
pg_dbname=trimet
pg_host=maps7.trimet.org

echo 'Enter PostGreSQL password:'
read -s PGPASSWORD
export PGPASSWORD

project_dir='G:/PUBLIC/GIS_Projects/System_Map/2015'
code_dir="${project_dir}/system-map-git"
mjr_roads_tbl=system_map_streets

generateStreetsTable() {
	sql_name="$1"
	streets_sql="${code_dir}/sql/${sql_name}"
	
	echo "psql -d $pg_dbname -U $pg_dbname -h $pg_host -f $streets_sql" 
	psql -d $pg_dbname -U $pg_user -h $pg_host -f "$streets_sql" 
}

exportStreetsToShp() {
	streets_tbl="$1"
	shp_name="$2"

	streets_shp="${project_dir}/shp/${shp_name}"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$streets_shp" $pg_dbname $streets_tbl
}

dropStreetsTable() {
	streets_tbl="$1"
	drop_cmd="DROP TABLE IF EXISTS $streets_tbl CASCADE;"

	echo "psql -d $pg_dbname -U $pg_dbname -h $pg_host -c $drop_cmd"
	psql -d $pg_dbname -U $pg_user -h $pg_host -c "$drop_cmd"
}

# # Get major roads for system map
# mjr_roads_tbl='system_map_streets'
# mjr_road_sql='get_major_roads_from_osm2pgsql.sql'
# mjr_roads_shp='system_map/osm2pgsql_major_roads.shp'

# generateStreetsTable "$mjr_roads_sql";
# exportStreetsToShp "$mjr_roads_tbl" "$mjr_roads_shp";
# dropStreetsTable "$mjr_roads_tbl";

# Get city center streets for system map inset
cc_streets_tbl='city_center_streets'
cc_streets_sql='get_city_center_streets_from_osm2pgsql.sql'
cc_streets_shp='city_center/streets_cc.shp'

generateStreetsTable "$cc_streets_sql";
exportStreetsToShp "$cc_streets_tbl" "$cc_streets_shp";
dropStreetsTable "$cc_streets_tbl";