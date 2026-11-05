begin;
-- A second owned candidate generator. Exact text matching is independent of
-- embedding similarity; source/version/citation and model-space guards remain.
create function public.search_published_keywords(p_text text,p_query jsonb,
  p_model text,p_revision text,p_dimensions integer,p_limit integer default 20)
returns table(source_id uuid,version_id uuid,title text,source_sha256 text,
  model_id text,model_revision text,dimensions integer,passage_id text,
  start_offset integer,end_offset integer,body text,similarity double precision)
language plpgsql security definer set search_path='' stable as $$
declare v_owner uuid:=auth.uid(); query_vector extensions.vector; terms pg_catalog.tsquery;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_text is null or octet_length(p_text) not between 1 and 8192 or btrim(p_text)=''
    or p_model is null or length(p_model) not between 1 and 200
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
  terms:=pg_catalog.websearch_to_tsquery('pg_catalog.simple'::pg_catalog.regconfig,p_text);
  if pg_catalog.numnode(terms)=0 then return; end if;
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
    where pg_catalog.to_tsvector('pg_catalog.simple'::pg_catalog.regconfig,e.text) @@ terms
    order by pg_catalog.ts_rank_cd(pg_catalog.to_tsvector('pg_catalog.simple'::pg_catalog.regconfig,e.text),terms) desc,
      e.sid,e.ordinal
    limit p_limit;
end $$;
revoke all on function public.search_published_keywords(text,jsonb,text,text,integer,integer)
  from public,anon,authenticated;
grant execute on function public.search_published_keywords(text,jsonb,text,text,integer,integer)
  to authenticated;
commit;
