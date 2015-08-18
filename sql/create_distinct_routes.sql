--(c) Grant Humphries for TriMet, 2015
--PostGreSQL Version: 9.3.5
--PostGIS Version: 2.1.4
----------------------------------

--Purpose:
--The TriMet transit routes as they are stored in our postgis databases are an amalgamation
--of all the patterns that compose a route bunched into a single geometry.  Even within a 
--single route there are usually many patterns that cover the same street segment meaning
--that route are composed of many overlapping lines.  This is not ideal for cartography so
--this script eliminates those duplicates and the result is a set of distinct, non-overlapping
--lines that form each route.

--1) conflate segments
--one of the complicating aspects of the process is that there are segments that are nearly
--identical and which should be merged, but that are slightly different than each other because
--hastus has broken some line segments at the location of stops (and thus added a new point that
--is not in the source segments that come from OpenStreetMap).  The solution to this is to add
--those hastus created points to all segments that are within one foot of them, making the 
--segments that were the same in OSM identical once again.

drop table if exists route_pt_dump cascade;
create table route_pt_dump as
--rush hour routes aren't officially tracked in trimet databases at this time so they're
--being added here, these whose full extent is rush hour, note that there are others for
--which only portions of them are rush hour: (30, 31, 32 34, 36, 72, 75, 87) on 2014 system map
	with rush_hour_routes (rush) as (
		values (1), (11), (18), (38), (50), (51), (53), (55), (59), 
			(61), (64), (65), (66), (68), (84), (92), (96), (99)),
	source_routes as (
		select row_number() over (order by rf.route_id) as id, 
			rf.geom, rf.route_id, r.type as route_type,
			case when rh.rush is not null then 'rush-hour'
				when rf.frequent is false then 'standard'
				when rf.frequent is true then 'frequent' end as serv_level
		from load.route_frequency rf
		left join load.route r
			on rf.route_id = r.id
			and rf.begin_date = r.begin_date
		left join rush_hour_routes rh
			on rf.route_id = rh.rush
		where current_date between rf.begin_date and rf.end_date)
--break routes into two vertex segments
--because many a these segment double back on each other and sometimes the hastus points
--are only a part of that double back the segments must be split at each vertex for the
--conflation to work properly
	select id, route_id, serv_level, route_type, (pd).geom as geom,
		(pd).path[1] as segment_id, (pd).path[2] as sequence_id
	from (
		select id, route_id, serv_level, route_type, ST_DumpPoints(geom) as pd
		from source_routes) temp_pt_dump;

alter table route_pt_dump add primary key (id, segment_id, sequence_id);

drop table if exists segmented_routes cascade;
create table segmented_routes as
	select pd1.route_id, pd1.serv_level, pd1.route_type, 
		ST_MakeLine(pd1.geom, pd2.geom) as geom
	from route_pt_dump pd1, route_pt_dump pd2
	where pd1.id = pd2.id
		and pd1.segment_id = pd2.segment_id
		and pd1.sequence_id = (pd2.sequence_id + 1);

alter table segmented_routes add id serial primary key;
create index seg_routes_gix on segmented_routes using GIST (geom);

drop table if exists unique_points cascade;
create table unique_points as
	select geom
	from route_pt_dump
	--group by must include x,y or some points will be lost due to 
	--imprecision of geom grouping
	group by ST_X(geom), ST_Y(geom), geom;

alter table unique_points add id serial primary key;
create index unique_pt_gix on unique_points using GIST (geom);

--snap segments to all points that are within 1 foot of them, including (and in
--particular) those that are not already a part of their geometry
drop table if exists conflated_segments cascade;
create table conflated_segments as
	select sr.id, sr.route_id, sr.serv_level, sr.route_type,
		ST_Snap(sr.geom, ST_Collect(up.geom), 1) as geom
	from segmented_routes sr, unique_points up
	where ST_DWithin(sr.geom, up.geom, 1)
	group by sr.id, sr.route_id, sr.serv_level, sr.geom;

--2) eliminate duplicate segments
--Decompose segments to their points then rebuild them a smaller segments containing two
--points each.  Compare these new segments and eliminate any duplicates

--dump the conflated segments to their constituent points
drop table if exists conflated_points cascade;
create table conflated_points as 
	select route_id, serv_level, route_type,
		id as segment_id, (dp).path[1] as sequence_id,
		ST_X((dp).geom) as x, ST_Y((dp).geom) as y
	from (
		select id, route_id, serv_level, route_type, ST_DumpPoints(geom) as dp
		from conflated_segments) route_pt_dump;

alter table conflated_points add primary key (segment_id, sequence_id);

--a) create a version of the routes that has with a single set of geometries for
--each line (no duplicate segments within the route and service level) 
drop table if exists distinct_routes cascade;
create table distinct_routes as 
	select route_id, serv_level, route_type, (ST_Dump(geom)).geom as geom
	from (
		select route_id, serv_level, route_type,
			ST_LineMerge(ST_Collect(ST_SetSRID(ST_MakeLine(
				ST_MakePoint(xy_array[1], xy_array[2]), 
				ST_MakePoint(xy_array[3], xy_array[4])), 2913))) as geom
		from (
			select cp1.route_id, cp1.route_type,
				case when 'frequent' = any(array_agg(cp1.serv_level)) then 'frequent'
					when 'standard' = any(array_agg(cp1.serv_level)) then 'standard'
					else 'rush-hour' end as serv_level,
				case when cp1.x < cp2.x then array[cp1.x, cp1.y, cp2.x, cp2.y]
					when cp1.x > cp2.x then array[cp2.x, cp2.y, cp1.x, cp1.y]
					--the 'y' cases are to handle the potential of the two x values being equal
					when cp1.y < cp2.y then array[cp1.x, cp1.y, cp2.x, cp2.y]
					else array[cp2.x, cp2.y, cp1.x, cp1.y] end as xy_array
			from conflated_points cp1, conflated_points cp2
			where cp1.segment_id = cp2.segment_id
				and cp1.sequence_id = (cp2.sequence_id + 1)
			group by cp1.route_id, cp1.route_type, xy_array) unique_xy
		group by route_id, serv_level, route_type) merged_segs;

--b) create a version of the routes that has a single set of geometries for each service
--level (for instance if two frequent service lines run along the same street there will only
--be a single geometry representin them both were the overlap)
drop table if exists service_level_routes cascade;
create table service_level_routes as 
	select routes, serv_level, route_type, (ST_Dump(geom)).geom as geom
	from (
		select routes, serv_level, route_type,
			ST_LineMerge(ST_Collect(ST_SetSRID(ST_MakeLine(
				ST_MakePoint(xy_array[1], xy_array[2]), 
				ST_MakePoint(xy_array[3], xy_array[4])), 2913))) as geom
		from (
			select cp1.serv_level, cp1.route_type, 
				array_to_string(array_agg(distinct cp1.route_id order by cp1.route_id), ',') as routes, 
				case when cp1.x < cp2.x then array[cp1.x, cp1.y, cp2.x, cp2.y]
					when cp1.x > cp2.x then array[cp2.x, cp2.y, cp1.x, cp1.y]
					--the 'y' cases are to handle the potential of the two x values being equal
					when cp1.y < cp2.y then array[cp1.x, cp1.y, cp2.x, cp2.y]
					else array[cp2.x, cp2.y, cp1.x, cp1.y] end as xy_array
			from conflated_points cp1, conflated_points cp2
			where cp1.segment_id = cp2.segment_id
				and cp1.sequence_id = (cp2.sequence_id + 1)
			group by cp1.serv_level, cp1.route_type, xy_array) unique_xy
		group by routes, serv_level, route_type) merged_segs;

--drop all intermediate tables
drop table if exists route_pt_dump cascade;
drop table if exists segmented_routes cascade;
drop table if exists unique_points cascade;
drop table if exists conflated_segments cascade;
drop table if exists conflated_points cascade;