--Grant Humphries, 2015
--PostGreSQL Version: 9.3.5
--PostGIS Version: 2.1.4
----------------------------------

--Purpose: I've manually updated the route changes that are not yet in Hastus, but
--will be implement in fall '15, this script will create a version of those routes
--that groups routes that run along the same street and have the same service level
--into a single geometry

drop table if exists route_pt_dump cascade;
create table route_pt_dump as 
	select route_id, serv_level, route_type, id, (pd).path[1] as segment_id, 
		(pd).path[2] as sequence_id, (pd).geom as geom
	from (
		select gid as id, route_id, serv_level, route_type, 
			ST_DumpPoints(geom) as pd
		from distinct_routes_fall15
		where geom && ST_MakeEnvelope(7638499.74714, 673309.064985, 
			7652208.08047,  688913.231652, 2913)) temp_dump;

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

--Merge any points that are with 0.1 feet of each other before snapping
--the segements to them, nodes that close to each other can cause problems
drop table if exists snap_points cascade;
create table snap_points as  
	with merged_points as ( 
		select up1.id, (sum(ST_X(up2.geom)) / count(*)) as x, 
			(sum(ST_Y(up2.geom)) / count(*)) as y
		from unique_points up1, unique_points up2
		where ST_DWithin(up1.geom, up2.geom, 0.1)
		group by up1.id)
	select ST_SetSRID(ST_MakePoint(x, y), 2913) as geom
	from merged_points
	group by x, y;

--snap segments to all points that are within 1 foot of them, including those that
--are not already a part of their geometry, this is to account for any minor
--inconsistencies that may have been introduced in the manual editing process
--for routes that travel along the same street
drop table if exists conflated_segments cascade;
create table conflated_segments as
	select sr.id, sr.route_id, sr.serv_level, sr.route_type,
		ST_Snap(sr.geom, ST_Collect(sp.geom), 1) as geom
	from segmented_routes sr, snap_points sp
	where ST_DWithin(sr.geom, sp.geom, 1)
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

--b) create a version of the routes that has a single set of geometries for each service
--level (for instance if two frequent service lines run along the same street there will 
--only be a single geometry representing them both were the overlap)
drop table if exists service_level_routes_fall15 cascade;
create table service_level_routes_fall15 as 
	select routes, serv_level, route_type, (ST_Dump(geom)).geom as geom
	from (
		select routes, serv_level, route_type,
			ST_Simplify(ST_LineMerge(ST_Collect(ST_SetSRID(ST_MakeLine(
				ST_MakePoint(xy_array[1], xy_array[2]), 
				ST_MakePoint(xy_array[3], xy_array[4])), 2913))), 0.1) as geom
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