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

project_dir='G:/PUBLIC/GIS_Projects/System_Map/2015'
code_dir="${project_dir}/system-map-git"

createDistinctRoutes() {
	distinct_sql="${code_dir}/sql/create_distinct_routes.sql"

	echo "psql -d $pg_dbname -h $pg_host -U $pg_user -f $distinct_sql"
	psql -d $pg_dbname -h $pg_host -U $pg_user -f "$distinct_sql"
}

exportToShapefile() {
	lines_table='distinct_routes'
	lines_shp="${project_dir}/shp/${lines_table}.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$lines_shp" $pg_dbname $lines_table

	service_table='service_level_routes'
	service_shp="${project_dir}/shp/${service_table}.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$service_shp" $pg_dbname $service_table
}

createDistinctRoutes;
exportToShapefile;