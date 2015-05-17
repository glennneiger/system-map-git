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

offset_table='offset_routes'
node_table='end_of_line_nodes'

loadOffsetRoutes() {
	oregon_spn='2913'
	offset_shp="${project_dir}/shp/offset_routes.shp"

	echo "shp2pgsql -s $oregon_spn -D -I $offset_shp $offset_table \
		| psql -q -h $pg_host -U $pg_user -d $pg_dbname"
	shp2pgsql -d -s $oregon_spn -D -I "$offset_shp" $offset_table \
		| psql -q -h $pg_host -U $pg_user -d $pg_dbname
}

createEndOfLineNodes() {
	end_of_line_sql="${code_dir}/sql/get_end_of_line_nodes.sql"

	echo "psql -h $pg_host -U $pg_user -d $pg_dbase -f $end_of_line_sql"
	psql -h $pg_host -U $pg_user -d $pg_dbname -f "$end_of_line_sql"
}

exportEndOfLineNodes() {
	nodes_shp="${project_dir}/shp/end_of_line_nodes.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$nodes_shp" $pg_dbname $node_table
}

dropPgTables() {
	tables=("$offset_table" "$node_table")

	for i in "${tables[@]}"
	do
		drop_cmd="DROP TABLE $i CASCADE;"
		echo "psql -h $pg_host -U $pg_user -d $pg_dbase -c $drop_cmd"
		psql -h $pg_host -U $pg_user -d $pg_dbname -c "$drop_cmd"
	done
}

loadOffsetRoutes;
#createEndOfLineNodes;
#exportEndOfLineNodes;
#dropPgTables;