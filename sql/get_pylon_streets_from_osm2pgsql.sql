drop table if exists pylon_streets cascade;
create table pylon_streets as
	with street_types (highway) as (
		values ('motorway'), ('motorway_link'), ('trunk'), ('trunk_link'),
			('primary'), ('primary_link'), ('secondary'), ('secondary_link'),
			('tertiary'), ('tertiary_link'), ('residential'), ('unclassified'),
			('service'), ('living_street'), ('track'), ('footway'), ('cycleway'),
			('path'), ('pedestrian'), ('steps'))
	select ST_Transform(way, 2913) as geom, 
		case when highway = 'construction' then construction
			else highway end as highway,
		label_text as abbr_name, osm_name, prefix as str_prefix,
		name as str_name, type as str_type, suffix as str_suffix, bridge, 
		tunnel, oneway, layer, ref, service
	from osmcarto._line l
	where exists (
		select null from street_types st
		where st.highway = l.highway
			or st.highway = l.construction)
		and way && ST_Transform(ST_MakeEnvelope(
			-123.2, 45.2, -122.2,  45.7, 4326), 3857)
		--exclude sidewalks and crosswalks
		and footway not in ('crossing', 'sidewalk')
		and path not in ('crossing', 'sidewalk')
		and cycleway not in ('crossing', 'sidewalk');