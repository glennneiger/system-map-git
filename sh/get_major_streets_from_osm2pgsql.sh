# !/bin/sh

pg_user=geoserve
pg_dbname=trimet
pg_host=maps7.trimet.org

echo 'Enter PostGreSQL password:'
read -s PGPASSWORD
export PGPASSWORD

project_dir='G:/PUBLIC/GIS_Projects/System_Map/2015'
mj_roads_tbl=system_map_streets

createMajorRoads() {
	mj_roads_sql="${project_dir}/sql/get_major_roads_from_osm2pgsql.sql"
	
	echo "psql -d $pg_dbname -U $pg_dbname -h $pg_host -f $mj_roads_sql" 
	psql -d $pg_dbname -U $pg_user -h $pg_host -f "$mj_roads_sql" 
}

exportToShp() {
	mj_roads_shp="${project_dir}/shp/osm2pgsql_major_roads.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$mj_roads_shp" $pg_dbname $mj_roads_tbl
}

dropMajorRoads() {
	drop_cmd="DROP TABLE IF EXISTS $mj_roads_tbl CASCADE;"

	echo "psql -d $pg_dbname -U $pg_dbname -h $pg_host -c $drop_cmd"
	psql -d $pg_dbname -U $pg_user -h $pg_host -c "$drop_cmd"
}

createMajorRoads;
exportToShp;
dropMajorRoads;