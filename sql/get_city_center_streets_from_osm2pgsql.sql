drop table if exists city_center_streets cascade;
create table city_center_streets as
	with street_types (highway) as (
		values ('motorway'), ('motorway_link'), ('trunk'), ('trunk_link'),
			('primary'), ('primary_link'), ('secondary'), ('secondary_link'),
			('tertiary'), ('tertiary_link'), ('residential'), ('unclassified'))
	select ST_Transform(way, 2913) as geom, 
		case when highway = 'construction'then construction
			else highway end as highway,
		label_text as abbr_name, osm_name, prefix as st_prefix,
		name as st_name, type as st_type, suffix as st_suffix, bridge, 
		tunnel, oneway, layer, ref, service
	from osmcarto._line l
	where (exists (
		select null from street_types st
		where st.highway = l.highway
			or st.highway = l.construction)
		or service = 'alley')
		and way && ST_Transform(ST_MakeEnvelope(7638499.74714, 
			673309.064985, 7652208.08047,  688913.231652, 2913), 3857);