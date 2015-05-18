# !/bin/bash

# Set postgres parameters
pg_dbname=trimet
pg_host=maps7.trimet.org
pg_user=geoserve
pg_schema=current

# Prompt the user to enter their postgres password, 'PGPASSWORD' is a keyword
# and will automatically set the password for most postgres commands in the
# current session
echo 'Enter PostGreSQL password:'
read -s PGPASSWORD
export PGPASSWORD

project_dir="G:/PUBLIC/GIS_Projects/System_Map/2015"

updateLandmarks() {
	landmark_table=landmark_ext
	landmark_shp="${project_dir}/shp/landmarks.shp"
	pgsql2shp -k -h $pg_host -u $pg_user -P $PGPASSWORD \
		-f "$landmark_shp" $pg_dbname $pg_schema.$landmark_table
}

updateLandmarks;