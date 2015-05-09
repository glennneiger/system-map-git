alter table distinct_routes add id serial primary key;
create index distinct_routes_gix on distinct_routes using GIST (geom);

drop table if exists turnarounds cascade;
create table turnarounds as
  with pseudo_turnarounds as (
    select min(id) as id, geom, min(route_type) as route_type,
      case when 'frequent' = any(array_agg(serv_level)) then 'frequent'
        when 'standard' = any(array_agg(serv_level)) then 'standard'
        else 'rush-hour' end as serv_level
    from (
      select id, ST_StartPoint(geom) as geom, serv_level, route_type
      from distinct_routes
        union all
      select id, ST_EndPoint(geom), serv_level, route_type
      from distinct_routes) end_pts
    --never group by geom alone as it has poor precision
    group by ST_X(geom), ST_Y(geom), geom
      having count(*) = 1)
  --this first query has a number of false positives that do end without other lines 
  --intersecting ther end points, but they're right on the top of the middle of other
  --lines, this second query eliminates all that don't visually look like turnarounds
  select *
  from pseudo_turnarounds pt
  where not exists (
    select null
    from distinct_routes dr
    where ST_DWithin(pt.geom, dr.geom, 1)
      and dr.id != pt.id);