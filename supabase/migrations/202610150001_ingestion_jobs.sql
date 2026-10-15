-- Durable scheduling prerequisite only: no ready transition, vectors or upload API.
begin;
create role gather_ingestion_worker nologin;
grant usage on schema gather_private to gather_ingestion_worker;

alter table public.source_versions add constraint version_owned_identity
  unique(id, source_id, owner_id);
create table gather_private.ingestion_targets (
  source_id uuid primary key,
  owner_id uuid not null,
  version_id uuid not null unique,
  foreign key(version_id,source_id,owner_id)
    references public.source_versions(id,source_id,owner_id) on delete cascade
);
create table gather_private.ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  source_id uuid not null,
  version_id uuid not null unique,
  request_key uuid not null,
  fingerprint bytea not null,
  input_bytes integer not null check(input_bytes between 1 and 65536),
  media_type text not null check(media_type in ('text/plain','text/markdown')),
  chunker_version text not null check(length(chunker_version) between 1 and 200),
  model_id text not null check(length(model_id) between 1 and 200),
  model_revision text not null check(length(model_revision) between 1 and 200),
  dimensions integer not null check(dimensions in (256,512,1024)),
  state text not null default 'queued' check(state in ('queued','processing','failed','cancelled')),
  attempts integer not null default 0 check(attempts between 0 and 3),
  next_attempt_at timestamptz not null default clock_timestamp(),
  lease_token uuid,
  lease_started_at timestamptz,
  lease_expires_at timestamptz,
  error_code text check(error_code in ('timeout','temporarily_unavailable','invalid_input','lease_expired','superseded','deleted')),
  created_at timestamptz not null default clock_timestamp(),
  unique(owner_id,request_key),
  foreign key(version_id,source_id,owner_id)
    references public.source_versions(id,source_id,owner_id) on delete cascade,
  check ((state='processing' and lease_token is not null and lease_started_at is not null
          and lease_expires_at is not null and lease_expires_at > lease_started_at)
    or (state<>'processing' and lease_token is null and lease_started_at is null and lease_expires_at is null))
);
create index ingestion_due on gather_private.ingestion_jobs(next_attempt_at,created_at)
  where state in ('queued','processing');
create index ingestion_source on gather_private.ingestion_jobs(source_id);
create index ingestion_live_leases on gather_private.ingestion_jobs(lease_expires_at)
  where state='processing';
revoke all on gather_private.ingestion_jobs, gather_private.ingestion_targets
  from public, anon, authenticated, gather_ingestion_worker;

-- Trusted coordinator only. It must verify original bytes/hash/type before calling.
-- No client or worker grant: this does not authorize an upload or trust client hashes.
create function gather_private.enqueue_text_job(p_owner uuid,p_source uuid,p_request uuid,
  p_sha256 text,p_parser text,p_bytes integer,p_media text,p_chunker text,
  p_model text,p_revision text,p_dimensions integer) returns uuid
language plpgsql security definer set search_path='' as $$
declare v_fingerprint bytea; v_job gather_private.ingestion_jobs%rowtype; v_version uuid; v_id uuid;
begin
  if p_owner is null or p_source is null or p_request is null or
    p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or
    p_parser is null or length(p_parser) not between 1 and 200 or
    p_bytes is null or p_bytes not between 1 and 65536 or
    p_media is null or p_media not in ('text/plain','text/markdown') or
    p_chunker is null or length(p_chunker) not between 1 and 200 or
    p_model is null or length(p_model) not between 1 and 200 or
    p_revision is null or length(p_revision) not between 1 and 200 or
    p_dimensions is null or p_dimensions not in (256,512,1024) then
    raise exception 'invalid_job' using errcode='22023';
  end if;
  -- Same quota -> source -> job lock order as save/delete/cleanup.
  perform 1 from gather_private.source_quotas where owner_id=p_owner for update;
  if not found then raise exception 'quota_not_configured' using errcode='P0001'; end if;
  perform 1 from public.sources where id=p_source and owner_id=p_owner
    and kind='file' and deleted_at is null for update;
  if not found then raise exception 'source_not_writable' using errcode='23503'; end if;
  v_fingerprint := sha256(convert_to(jsonb_build_array(p_source,p_sha256,p_parser,p_bytes,
    p_media,p_chunker,p_model,p_revision,p_dimensions)::text,'UTF8'));
  select * into v_job from gather_private.ingestion_jobs where owner_id=p_owner and request_key=p_request;
  if found then
    if v_job.fingerprint<>v_fingerprint then raise exception 'request_key_conflict' using errcode='22023'; end if;
    return v_job.id;
  end if;
  -- Bound retained scheduling metadata. No eviction or silent receipt loss.
  if (select count(*) from gather_private.ingestion_jobs where source_id=p_source)>=16 then
    raise exception 'version_limit_reached' using errcode='P0001';
  end if;
  insert into public.source_versions(source_id,owner_id,content_sha256,parser_version)
    values(p_source,p_owner,p_sha256,p_parser) returning id into v_version;
  update gather_private.ingestion_jobs set state='cancelled',error_code='superseded',
    lease_token=null,lease_started_at=null,lease_expires_at=null where source_id=p_source;
  insert into gather_private.ingestion_jobs(owner_id,source_id,version_id,request_key,fingerprint,
    input_bytes,media_type,chunker_version,model_id,model_revision,dimensions)
    values(p_owner,p_source,v_version,p_request,v_fingerprint,p_bytes,p_media,p_chunker,p_model,p_revision,p_dimensions)
    returning id into v_id;
  insert into gather_private.ingestion_targets values(p_source,p_owner,v_version)
    on conflict(source_id) do update set version_id=excluded.version_id;
  return v_id;
end $$;

create function gather_private.cancel_deleted_jobs() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if new.deleted_at is not null then
    update gather_private.ingestion_jobs set state='cancelled',error_code='deleted',
      lease_token=null,lease_started_at=null,lease_expires_at=null where source_id=new.id;
  end if;
  return new;
end $$;
create trigger ingestion_tombstone after update of deleted_at on public.sources
  for each row execute function gather_private.cancel_deleted_jobs();

create function gather_private.freeze_job_version() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if exists(select 1 from gather_private.ingestion_jobs where version_id=old.id) then
    raise exception 'version_immutable' using errcode='23514';
  end if;
  return new;
end $$;
create trigger ingestion_version_immutable before update on public.source_versions
  for each row execute function gather_private.freeze_job_version();

-- One global live lease, consistent with the measured single-flight CPU runtime.
-- The advisory lock serializes claims; source SKIP LOCKED avoids waiting for deletion.
-- At most one expired/exhausted candidate is retired per call; dispatcher polls again.
create function gather_private.claim_text_job() returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_source uuid; v_job gather_private.ingestion_jobs%rowtype; v_now timestamptz;
begin
  if not pg_try_advisory_xact_lock(714011,1) then return null; end if;
  v_now:=clock_timestamp();
  if exists(select 1 from gather_private.ingestion_jobs where state='processing' and lease_expires_at>v_now) then return null; end if;
  select s.id into v_source from public.sources s
    join gather_private.ingestion_targets t on t.source_id=s.id
    join gather_private.ingestion_jobs j on j.version_id=t.version_id
    where s.deleted_at is null and ((j.state='queued' and j.next_attempt_at<=v_now)
      or (j.state='processing' and j.lease_expires_at<=v_now))
    order by j.next_attempt_at,j.created_at,j.id limit 1 for update of s skip locked;
  if not found then return null; end if;
  select j.* into v_job from gather_private.ingestion_jobs j
    join gather_private.ingestion_targets t on t.version_id=j.version_id
    where t.source_id=v_source for update of j;
  v_now:=clock_timestamp();
  if v_job.id is null or not ((v_job.state='queued' and v_job.next_attempt_at<=v_now)
    or (v_job.state='processing' and v_job.lease_expires_at<=v_now)) then return null; end if;
  if v_job.attempts>=3 then
    update gather_private.ingestion_jobs set state='failed',error_code='lease_expired',
      lease_token=null,lease_started_at=null,lease_expires_at=null where id=v_job.id;
    return null;
  end if;
  update gather_private.ingestion_jobs set state='processing',attempts=attempts+1,
    lease_token=gen_random_uuid(),lease_started_at=v_now,lease_expires_at=v_now+interval '60 seconds',
    error_code=case when state='processing' then 'lease_expired' else error_code end
    where id=v_job.id returning * into v_job;
  return (to_jsonb(v_job)-'fingerprint') || (select jsonb_build_object(
    'content_sha256',content_sha256,'parser_version',parser_version)
    from public.source_versions where id=v_job.version_id);
end $$;

-- Fencing helper, internal only. Keep parent lock until caller transaction commits.
create function gather_private.lock_live_job(p_job uuid,p_token uuid)
returns gather_private.ingestion_jobs
language plpgsql security definer set search_path='' as $$
declare v_source uuid; v_job gather_private.ingestion_jobs%rowtype;
begin
  select source_id into v_source from gather_private.ingestion_jobs where id=p_job;
  perform 1 from public.sources where id=v_source and deleted_at is null for update;
  if not found then raise exception 'stale_lease' using errcode='55000'; end if;
  select j.* into v_job from gather_private.ingestion_jobs j
    join gather_private.ingestion_targets t on t.version_id=j.version_id
    where j.id=p_job for update of j;
  if not found or v_job.state<>'processing' or p_token is null or
    v_job.lease_token<>p_token or v_job.lease_expires_at<=clock_timestamp() then
    raise exception 'stale_lease' using errcode='55000';
  end if;
  return v_job;
end $$;

create function gather_private.renew_text_job(p_job uuid,p_token uuid) returns timestamptz
language plpgsql security definer set search_path='' as $$
declare v_job gather_private.ingestion_jobs%rowtype; v_until timestamptz;
begin
  v_job:=gather_private.lock_live_job(p_job,p_token);
  v_until:=least(clock_timestamp()+interval '60 seconds',v_job.lease_started_at+interval '5 minutes');
  update gather_private.ingestion_jobs set lease_expires_at=v_until where id=p_job;
  return v_until;
end $$;

create function gather_private.fail_text_job(p_job uuid,p_token uuid,p_error text) returns text
language plpgsql security definer set search_path='' as $$
declare v_job gather_private.ingestion_jobs%rowtype; v_state text;
begin
  if p_error is null or p_error not in ('timeout','temporarily_unavailable','invalid_input') then
    raise exception 'invalid_error_code' using errcode='22023';
  end if;
  v_job:=gather_private.lock_live_job(p_job,p_token);
  v_state:=case when p_error='invalid_input' or v_job.attempts>=3 then 'failed' else 'queued' end;
  update gather_private.ingestion_jobs set state=v_state,error_code=p_error,
    next_attempt_at=clock_timestamp()+make_interval(secs=>5*power(2,v_job.attempts-1)+random()*5),
    lease_token=null,lease_started_at=null,lease_expires_at=null where id=p_job;
  return v_state;
end $$;

-- Owner-scoped read without lease capabilities or worker metadata leakage.
create function public.source_processing_status(p_source uuid)
returns table(job_id uuid,version_id uuid,state text,attempts integer,error_code text)
language sql security definer set search_path='' stable as $$
  select j.id,j.version_id,j.state,j.attempts,j.error_code
  from gather_private.ingestion_jobs j
  join gather_private.ingestion_targets t on t.version_id=j.version_id
  join public.sources s on s.id=t.source_id
  where s.id=p_source and s.owner_id=auth.uid() and s.deleted_at is null
$$;

revoke all on function
  gather_private.enqueue_text_job(uuid,uuid,uuid,text,text,integer,text,text,text,text,integer),
  gather_private.cancel_deleted_jobs(),gather_private.freeze_job_version(),
  gather_private.claim_text_job(),gather_private.lock_live_job(uuid,uuid),
  gather_private.renew_text_job(uuid,uuid),gather_private.fail_text_job(uuid,uuid,text)
  from public, anon, authenticated, gather_ingestion_worker;
revoke all on function public.source_processing_status(uuid) from public, anon, authenticated;
grant execute on function public.source_processing_status(uuid) to authenticated;
grant execute on function gather_private.claim_text_job(),
  gather_private.renew_text_job(uuid,uuid),gather_private.fail_text_job(uuid,uuid,text)
  to gather_ingestion_worker;
commit;
