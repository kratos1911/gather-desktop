-- Metadata only. Eligibility is a hint; exact-attempt recovery still locks and rechecks.
begin;
create function gather_private.can_resume_text_job(p_job uuid) returns boolean
language sql stable set search_path='' as $$
  select exists(select 1 from gather_private.ingestion_jobs j
    join gather_private.automatic_text_jobs a on a.job_id=j.id
    join gather_private.ingestion_targets t on t.version_id=j.version_id and t.source_id=j.source_id
    join public.sources s on s.id=j.source_id
    where j.id=p_job and j.owner_id=auth.uid() and s.owner_id=auth.uid()
      and s.deleted_at is null and j.attempts<3
      and ((j.state='queued' and j.next_attempt_at<=clock_timestamp())
        or (j.state='processing' and j.lease_expires_at<=clock_timestamp())))
$$;
revoke all on function gather_private.can_resume_text_job(uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;

create function public.list_library_sources_with_recovery(p_limit integer default 20,
  p_before_created_at timestamptz default null,p_before_id uuid default null)
returns table(source_id uuid,title text,kind text,created_at text,
  published_version_id uuid,processing_version_id uuid,job_id uuid,
  state text,attempts integer,error_code text,can_resume boolean)
language sql security definer stable set search_path='' as $$
  select l.*,gather_private.can_resume_text_job(l.job_id)
  from public.list_library_sources(p_limit,p_before_created_at,p_before_id) l
  order by l.created_at desc,l.source_id desc
$$;

create function public.source_processing_status_with_recovery(p_source uuid)
returns table(job_id uuid,version_id uuid,state text,attempts integer,error_code text,can_resume boolean)
language sql security definer stable set search_path='' as $$
  select j.*,gather_private.can_resume_text_job(j.job_id)
  from public.source_processing_status(p_source) j
$$;
revoke all on function public.list_library_sources_with_recovery(integer,timestamptz,uuid),
  public.source_processing_status_with_recovery(uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function public.list_library_sources_with_recovery(integer,timestamptz,uuid),
  public.source_processing_status_with_recovery(uuid) to authenticated;
commit;
