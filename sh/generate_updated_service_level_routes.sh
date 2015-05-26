# !/bin/bash

# Set postgres parameters
pg_dbname=trimet
pg_host=maps7.trimet.org
pg_user=geoserve

# Prompt the user to enter their postgres password, 'PGPASSWORD' is a keyword
# and will automatically set the password for most postgres commands in the
# current session
echo 'Enter PostGreSQL password:'
read -s PGPASSWORD
export PGPASSWORD

project_dir="G:/PUBLIC/GIS_Projects/System_Map/2015"
code_dir="${project_dir}/system-map-git"

u_routes_tbl='distinct_routes_fall15'
sr_routes_tbl='service_level_routes_fall15'

loadUpdatedRoutes() {
	oregon_spn='2913'
	u_routes_shp="${project_dir}/shp/system_map/distinct_routes_fall15.shp"

	shp2pgsql -d -s $oregon_spn -D -I "$u_routes_shp" $u_routes_tbl \
		| psql -q -h $pg_host -U $pg_user -d $pg_dbname
}

createServiceLevelRoutes() {
	serv_level_sql="${code_dir}/sql/generate_updated_service_level_routes.sql"

	echo "psql -d $pg_dbname -h $pg_host -U $pg_user -f $serv_level_sql"
	psql -d $pg_dbname -h $pg_host -U $pg_user -f "$serv_level_sql"
}

exportRoutesToShapefile() {
	sr_routes_shp="${project_dir}/shp/system_map/${sr_routes_tbl}.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$sr_routes_shp" $pg_dbname $sr_routes_tbl
}

dropRouteTables() {
	tables=("$u_routes_tbl" "$sr_routes_tbl")

	for i in "${tables[@]}"
	do
		drop_cmd="DROP TABLE IF EXISTS $i CASCADE;"
		echo "psql -h $pg_host -U $pg_user -d $pg_dbase -c $drop_cmd"
		psql -h $pg_host -U $pg_user -d $pg_dbname -c "$drop_cmd"
	done
}

loadUpdatedRoutes;
createServiceLevelRoutes;
exportRoutesToShapefile;
dropRouteTables;