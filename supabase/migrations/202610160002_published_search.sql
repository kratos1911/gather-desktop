begin;
-- Auth/PostgREST supplies the identity. No caller-controlled owner parameter.
-- Exact cosine ranking for the initial bounded library; no ANN approximation.
create function public.search_published_text(p_query jsonb,p_model text,p_revision text,
  p_dimensions integer,p_limit integer default 20)
returns table(source_id uuid,version_id uuid,title text,source_sha256 text,
  model_id text,model_revision text,dimensions integer,passage_id text,
  start_offset integer,end_offset integer,body text,similarity double precision)
language plpgsql security definer set search_path='' stable as $$
declare v_owner uuid:=auth.uid(); query_vector extensions.vector;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_model is null or length(p_model) not between 1 and 200
    or p_revision is null or length(p_revision) not between 1 and 200
    or p_dimensions is null or p_dimensions not in (256,512,1024)
    or p_limit is null or p_limit not between 1 and 100
    or p_query is null or jsonb_typeof(p_query)<>'array' or octet_length(p_query::text)>65536 then
    raise exception 'invalid_query' using errcode='22023'; end if;
  if jsonb_array_length(p_query)<>p_dimensions or exists(
    select 1 from jsonb_array_elements(p_query) x where jsonb_typeof(x)<>'number') then
    raise exception 'invalid_query' using errcode='22023'; end if;
  query_vector:=p_query::text::extensions.vector;
  if abs(extensions.vector_norm(query_vector)-1)>0.001 then
    raise exception 'invalid_query' using errcode='22023'; end if;
  return query
    with eligible as materialized (
      select s.id sid,p.version_id vid,s.title heading,v.content_sha256 hash,
        j.model_id model,j.model_revision revision,j.dimensions dims,
        c.passage_id pid,c.ordinal,c.start_offset a,c.end_offset b,c.body text,c.embedding
      from gather_private.published_sources p
      join public.sources s on s.id=p.source_id
      join public.source_versions v on v.id=p.version_id
      join gather_private.ingestion_jobs j on j.id=p.job_id
      join gather_private.staged_passages c on c.version_id=p.version_id
      where s.owner_id=v_owner and s.deleted_at is null
        and j.model_id=p_model and j.model_revision=p_revision and j.dimensions=p_dimensions
        and c.embedding is not null
    )
    select e.sid,e.vid,e.heading,e.hash,e.model,e.revision,e.dims,e.pid,e.a,e.b,e.text,
      1-(e.embedding operator(extensions.<=>) query_vector)
    from eligible e
    order by e.embedding operator(extensions.<=>) query_vector,e.sid,e.ordinal
    limit p_limit;
end $$;

-- Version is required: an old search citation must not silently open new content.
-- Missing, foreign-owned, unpublished, replaced and deleted versions all return [].
create function public.open_published_text(p_source uuid,p_version uuid)
returns table(source_id uuid,version_id uuid,title text,source_sha256 text,
  parser_version text,chunker_version text,model_id text,model_revision text,
  dimensions integer,body text,passages jsonb)
language sql security definer set search_path='' stable as $$
  select s.id,p.version_id,s.title,v.content_sha256,v.parser_version,j.chunker_version,
    j.model_id,j.model_revision,j.dimensions,t.body,
    (select jsonb_agg(jsonb_build_object('id',c.passage_id,'start',c.start_offset,'end',c.end_offset)
      order by c.ordinal) from gather_private.staged_passages c where c.version_id=p.version_id)
  from gather_private.published_sources p
  join public.sources s on s.id=p.source_id
  join public.source_versions v on v.id=p.version_id
  join gather_private.ingestion_jobs j on j.id=p.job_id
  join gather_private.staged_text t on t.version_id=p.version_id
  where s.id=p_source and p.version_id=p_version and s.owner_id=auth.uid() and s.deleted_at is null
$$;
revoke all on function public.search_published_text(jsonb,text,text,integer,integer),
 public.open_published_text(uuid,uuid) from public,anon,authenticated;
grant execute on function public.search_published_text(jsonb,text,text,integer,integer),
 public.open_published_text(uuid,uuid) to authenticated;
commit;
