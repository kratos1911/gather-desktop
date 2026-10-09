begin;
create schema gather_private;
revoke all on schema gather_private from public, anon, authenticated;

-- Administrators provision limits explicitly; no automatic production allowance.
create table gather_private.source_quotas (
  owner_id uuid primary key references auth.users(id),
  source_limit integer not null check (source_limit >= 0),
  used integer not null default 0 check (used >= 0 and used <= source_limit)
);
create table gather_private.save_receipts (
  owner_id uuid not null references auth.users(id),
  request_key uuid not null,
  source_id uuid not null unique,
  fingerprint bytea not null,
  primary key (owner_id, request_key)
);
create table gather_private.cleanup_requests (
  source_id uuid primary key,
  owner_id uuid not null,
  created_at timestamptz not null default now(),
  foreign key (source_id, owner_id) references public.sources(id, owner_id)
);
revoke all on all tables in schema gather_private from public, anon, authenticated;

create function public.save_source(p_request_key uuid, p_kind text, p_title text,
  p_notes text default '', p_url text default null) returns uuid
language plpgsql security definer set search_path = '' as $$
declare
  v_owner uuid := auth.uid();
  v_quota gather_private.source_quotas%rowtype;
  v_receipt gather_private.save_receipts%rowtype;
  v_id uuid;
  v_fingerprint bytea;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_request_key is null then raise exception 'request_key_required' using errcode='22023'; end if;
  -- Bound input before constructing the fingerprint; table constraints validate shape.
  if p_kind is null or p_title is null or p_notes is null or
     length(p_kind)>20 or length(p_title)>500 or length(p_notes)>16000 or length(p_url)>8192 then
    raise exception 'invalid_source' using errcode='22023';
  end if;
  select * into v_quota from gather_private.source_quotas where owner_id=v_owner for update;
  if not found then raise exception 'quota_not_configured' using errcode='P0001'; end if;
  v_fingerprint := sha256(convert_to(jsonb_build_array(p_kind,p_title,p_notes,p_url)::text,'UTF8'));
  select * into v_receipt from gather_private.save_receipts where owner_id=v_owner and request_key=p_request_key;
  if found then
    if v_receipt.fingerprint <> v_fingerprint then
      raise exception 'request_key_conflict' using errcode='22023';
    end if;
    -- Receipt survives deletion: a late retry returns the old ID, never resurrects it.
    return v_receipt.source_id;
  end if;
  if v_quota.used >= v_quota.source_limit then raise exception 'source_quota_exceeded' using errcode='P0001'; end if;
  insert into public.sources(owner_id,kind,title,notes,original_url)
    values(v_owner,p_kind,p_title,p_notes,p_url) returning id into v_id;
  insert into gather_private.save_receipts values(v_owner,p_request_key,v_id,v_fingerprint);
  update gather_private.source_quotas set used=used+1 where owner_id=v_owner;
  return v_id;
end $$;

create function public.request_source_deletion(p_source_id uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
declare v_owner uuid := auth.uid();
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  -- All lifecycle operations lock quota then source to avoid inconsistent lock order.
  perform 1 from gather_private.source_quotas where owner_id=v_owner for update;
  perform 1 from public.sources where id=p_source_id and owner_id=v_owner for update;
  if not found then return false; end if;
  update public.sources set deleted_at=coalesce(deleted_at,now()) where id=p_source_id and owner_id=v_owner;
  insert into gather_private.cleanup_requests(source_id,owner_id) values(p_source_id,v_owner)
    on conflict(source_id) do nothing;
  return true;
end $$;

-- Privileged, DATABASE-ONLY cleanup. No Storage objects exist in this slice.
-- Do not call this once external assets exist without verified external cleanup.
create function gather_private.finish_source_cleanup(p_source_id uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
declare v_owner uuid; v_accounted boolean;
begin
  select owner_id into v_owner from gather_private.cleanup_requests where source_id=p_source_id;
  if not found then return false; end if;
  perform 1 from gather_private.source_quotas where owner_id=v_owner for update;
  perform 1 from public.sources where id=p_source_id and owner_id=v_owner and deleted_at is not null for update;
  if not found then return false; end if;
  select exists(select 1 from gather_private.save_receipts where source_id=p_source_id and owner_id=v_owner) into v_accounted;
  delete from public.source_versions where source_id=p_source_id and owner_id=v_owner;
  delete from gather_private.cleanup_requests where source_id=p_source_id and owner_id=v_owner;
  delete from public.sources where id=p_source_id and owner_id=v_owner;
  if v_accounted then update gather_private.source_quotas set used=used-1 where owner_id=v_owner; end if;
  return true;
end $$;

create function gather_private.guard_version_write() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  -- Serialize derivative writes with tombstones; FK alone permits deleted parents.
  perform 1 from public.sources where id=new.source_id and owner_id=new.owner_id
    and deleted_at is null for update;
  if not found then raise exception 'source_not_writable' using errcode='23503'; end if;
  return new;
end $$;
create trigger source_version_live_parent before insert or update on public.source_versions
  for each row execute function gather_private.guard_version_write();

revoke all on function public.save_source(uuid,text,text,text,text) from public, anon, authenticated;
revoke all on function public.request_source_deletion(uuid) from public, anon, authenticated;
revoke all on all functions in schema gather_private from public, anon, authenticated;
grant execute on function public.save_source(uuid,text,text,text,text) to authenticated;
grant execute on function public.request_source_deletion(uuid) to authenticated;
commit;
