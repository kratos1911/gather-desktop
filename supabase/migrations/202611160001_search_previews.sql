begin;

-- Rank in the same database snapshot. Reuse the two published rankers to keep
-- tie order and relevance inputs stable, then send bounded, cited passage slices.
create function public.search_published_previews(p_text text,p_query jsonb,
  p_model text,p_revision text,p_dimensions integer,p_limit integer default 20)
returns jsonb language plpgsql security definer set search_path='' stable as $$
declare
  v_owner uuid := auth.uid();
  reply jsonb;
begin
  if v_owner is null then
    raise exception 'authentication_required' using errcode='42501';
  end if;
  if p_limit is null or p_limit not between 1 and 20 or
     p_text is null or octet_length(p_text) not between 1 and 8192 or btrim(p_text)='' then
    raise exception 'invalid_query' using errcode='22023';
  end if;
  with ranked as (
    select 'semantic'::text as branch, s.*
    from public.search_published_text(p_query,p_model,p_revision,p_dimensions,p_limit)
      with ordinality s
    union all
    select 'keywords'::text as branch, k.*
    from public.search_published_keywords(p_text,p_query,p_model,p_revision,p_dimensions,p_limit)
      with ordinality k
  ), sliced as (
    select r.*, j.media_type,
      r.start_offset + start_at.relative_start as preview_start,
      substring(r.body from start_at.relative_start + 1 for 240) as preview,
      case j.media_type
        when 'application/pdf' then pdf.pages
        when 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' then docx.paragraphs
        when 'image/png' then img.metadata->'regions'
        when 'image/jpeg' then img.metadata->'regions'
      end as location_spans
    from ranked r
    join public.sources s on s.id=r.source_id and s.owner_id=v_owner and s.deleted_at is null
    join gather_private.published_sources p on p.source_id=r.source_id and p.version_id=r.version_id
    join gather_private.ingestion_jobs j on j.id=p.job_id
    left join gather_private.pdf_text pdf on pdf.version_id=p.version_id
    left join gather_private.docx_text docx on docx.version_id=p.version_id
    left join gather_private.image_text img on img.version_id=p.version_id
    cross join lateral (select strpos(lower(r.body),lower(btrim(p_text))) as position) match_at
    cross join lateral (
      select greatest(
        length(substring(r.body from '^[[:space:]]*')),
        match_at.position-33
      ) as initial_start
    ) initial
    cross join lateral (
      select initial.initial_start + case
        when initial.initial_start > 0
          and substring(r.body from initial.initial_start for 1) !~ '[[:space:]]'
          and substring(r.body from initial.initial_start + 1 for 1) !~ '[[:space:]]'
        then coalesce(length(substring(
          substring(r.body from initial.initial_start + 1
            for greatest(0,match_at.position-initial.initial_start-1))
          from '^[^[:space:]]+[[:space:]]+')),0)
        else 0
      end as relative_start
    ) start_at
  ), payloads as (
    select c.branch,c.ordinality,
      jsonb_build_object(
        'source_id',c.source_id,'version_id',c.version_id,'title',c.title,
        'source_sha256',c.source_sha256,'model_id',c.model_id,
        'model_revision',c.model_revision,'dimensions',c.dimensions,
        'passage_id',c.passage_id,'similarity',c.similarity,'media_type',c.media_type,
        'body',c.preview,'start_offset',c.preview_start,
        'end_offset',c.preview_start+length(c.preview),'locations',loc.numbers
      ) as item
    from sliced c
    cross join lateral (
      select coalesce(jsonb_agg((span->>'number')::integer order by (span->>'number')::integer),'[]'::jsonb) as numbers
      from jsonb_array_elements(c.location_spans) span
      where (span->>'start')::integer < c.preview_start+length(c.preview)
        and (span->>'end')::integer > c.preview_start
    ) loc
  )
  select jsonb_build_object(
    'semantic',coalesce(jsonb_agg(item order by ordinality) filter(where branch='semantic'),'[]'::jsonb),
    'keywords',coalesce(jsonb_agg(item order by ordinality) filter(where branch='keywords'),'[]'::jsonb)
  ) into reply from payloads;
  return reply;
end $$;

revoke all on function public.search_published_previews(text,jsonb,text,text,integer,integer)
  from public,anon,authenticated;
grant execute on function public.search_published_previews(text,jsonb,text,text,integer,integer)
  to authenticated;
commit;
