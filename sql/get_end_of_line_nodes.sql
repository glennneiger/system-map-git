drop table if exists end_of_line_nodes cascade;
create table end_of_line_nodes as
  --ST_StartPoint and ST_EndPoint don't work on multigeometries so these multiline
  --strings must first be dumped to linestring
  with offset_dump as (
    select row_number() over (order by gid) as id, 
      route_type, serv_level, (ST_Dump(geom)).geom as geom
    from offset_routes),
  pseudo_nodes as (
    select min(id) as id, geom, serv_level, min(route_type) as route_type
    from (
      select id, ST_StartPoint(geom) as geom, serv_level, route_type
      from offset_dump
        union all
      select id, ST_EndPoint(geom), serv_level, route_type
      from offset_dump) end_pts
    --never group by geom alone as it has poor precision
    group by ST_X(geom), ST_Y(geom), geom, serv_level
      having count(*) = 1)
  --this first query has a number of false positives that do end without other lines 
  --intersecting ther end points, but they're right on the top of the middle of other
  --lines, this second query eliminates all that don't visually look like turnarounds
  select geom, min(route_type) as route_type,
    case when 'frequent' = any(array_agg(serv_level)) then 'frequent'
      when 'standard' = any(array_agg(serv_level)) then 'standard'
      when 'rush-hour' = any(array_agg(serv_level)) then 'rush-hour'
      else 'error' end as serv_level
  from pseudo_nodes pn
  where not exists (
    select null
    from offset_dump od
    where ST_DWithin(pn.geom, od.geom, 1)
      and od.id != pn.id
      and (od.serv_level = pn.serv_level
      or (od.serv_level != pn.serv_level and pn.serv_level != 'frequent')))
  group by ST_X(geom), ST_Y(geom), geom;