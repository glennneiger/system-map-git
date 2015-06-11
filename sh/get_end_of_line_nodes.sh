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
	offset_shp="$1"

	shp2pgsql -d -s $oregon_spn -D -I "$offset_shp" $offset_table \
		| psql -q -h $pg_host -U $pg_user -d $pg_dbname
}

createEndOfLineNodes() {
	end_of_line_sql="${code_dir}/sql/get_end_of_line_nodes.sql"

	echo "psql -h $pg_host -U $pg_user -d $pg_dbase -f $end_of_line_sql"
	psql -h $pg_host -U $pg_user -d $pg_dbname -f "$end_of_line_sql"
}

exportEndOfLineNodes() {
	nodes_shp="$1"
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

while true; do
	read -p 'Which map do you wish to generate nodes for (sm or cc)?' map
	case $map in
	sm)	sm_offset_routes="${project_dir}/shp/system_map/offset_routes.shp"
		loadOffsetRoutes "$sm_offset_routes";
		createEndOfLineNodes;

		sm_eol_nodes="${project_dir}/shp/system_map/end_of_line_nodes.shp"
		exportEndOfLineNodes "$sm_eol_nodes";
		dropPgTables;
		break;;
	
	cc)	cc_offset_routes="${project_dir}/shp/city_center/combined_routes_cc.shp"
		loadOffsetRoutes "$cc_offset_routes";
		createEndOfLineNodes;

		cc_eol_nodes="${project_dir}/shp/city_center/end_of_line_nodes_cc.shp"
		exportEndOfLineNodes "$cc_eol_nodes";
		dropPgTables;
		break;;
	
	*) echo "Enter 'sm' for system map or 'cc' for city center"
	esac
done