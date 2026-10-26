begin;
-- A cursor is only a position. Auth-derived ownership is applied on every page,
-- including when another user's valid timestamp/UUID is supplied as that position.
create function public.list_library_sources(p_limit integer default 20,
  p_before_created_at timestamptz default null,p_before_id uuid default null)
returns table(source_id uuid,title text,kind text,created_at text,
  published_version_id uuid,processing_version_id uuid,job_id uuid,
  state text,attempts integer,error_code text)
language plpgsql security definer set search_path='' stable as $$
declare v_owner uuid:=auth.uid();
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_limit is null or p_limit not between 1 and 20
    or (p_before_created_at is null)<>(p_before_id is null)
    or (p_before_created_at is not null and not isfinite(p_before_created_at)) then
    raise exception 'invalid_cursor' using errcode='22023'; end if;
  return query
    select s.id,s.title,s.kind,
      to_char(s.created_at at time zone 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
      p.version_id,t.version_id,j.id,j.state,j.attempts,j.error_code
    from public.sources s
    left join gather_private.published_sources p on p.source_id=s.id
    left join gather_private.ingestion_targets t on t.source_id=s.id and t.owner_id=s.owner_id
    left join gather_private.ingestion_jobs j on j.version_id=t.version_id
      and j.source_id=s.id and j.owner_id=s.owner_id
    where s.owner_id=v_owner and s.deleted_at is null
      and (p_before_created_at is null or (s.created_at,s.id)<(p_before_created_at,p_before_id))
    order by s.created_at desc,s.id desc
    limit p_limit+1; -- One bounded lookahead row, removed by the application.
end $$;
revoke all on function public.list_library_sources(integer,timestamptz,uuid)
  from public,anon,authenticated;
grant execute on function public.list_library_sources(integer,timestamptz,uuid) to authenticated;
commit;
