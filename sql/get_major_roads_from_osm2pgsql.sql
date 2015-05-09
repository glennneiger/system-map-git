drop table if exists system_map_streets cascade;
create table system_map_streets as
	select ST_Transform(way, 2913) as geom, highway, osm_name, ref, prefix, name, type, suffix, 
		tags -> 'motorway_link' as mtrwy_link
	from osmcarto.tm_osm_line
	where highway in ('motorway', 'motorway_link', 'trunk', 'trunk_link',
		'primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary',
		'tertiary_link');