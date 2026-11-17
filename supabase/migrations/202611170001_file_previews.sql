begin;

create function public.list_library_file_previews(p_limit integer default 20,
  p_before_created_at timestamptz default null,p_before_id uuid default null)
returns table(source_id uuid,title text,kind text,created_at text,
  published_version_id uuid,processing_version_id uuid,job_id uuid,
  state text,attempts integer,error_code text,can_resume boolean,preview text)
language sql security definer stable set search_path='' as $$
  select l.*,nullif(left(btrim(t.body,E'\t\r\n '),240),'')
  from public.list_library_sources_with_recovery(p_limit,p_before_created_at,p_before_id) l
  left join gather_private.staged_text t on t.version_id=l.published_version_id
  order by l.created_at desc,l.source_id desc
$$;

create function public.read_published_original(p_source uuid,p_version uuid)
returns jsonb language sql security definer stable set search_path='' as $$
  select jsonb_build_object('source_id',s.id,'version_id',p.version_id,'title',s.title,
    'media_type',j.media_type,'source_sha256',v.content_sha256,
    'content_base64',replace(encode(t.original,'base64'),E'\n',''))
  from gather_private.published_sources p
  join public.sources s on s.id=p.source_id
  join public.source_versions v on v.id=p.version_id
  join gather_private.staged_text t on t.version_id=p.version_id
  join gather_private.ingestion_jobs j on j.id=p.job_id
  where s.owner_id=auth.uid() and s.deleted_at is null and s.id=p_source and p.version_id=p_version
$$;

revoke all on function public.list_library_file_previews(integer,timestamptz,uuid),
  public.read_published_original(uuid,uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function public.list_library_file_previews(integer,timestamptz,uuid),
  public.read_published_original(uuid,uuid) to authenticated;
commit;
