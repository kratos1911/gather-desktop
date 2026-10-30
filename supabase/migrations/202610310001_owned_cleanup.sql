-- Owner-authorized database-only cleanup. Existing Storage guard and replay
-- receipts remain authoritative; no direct private-table grants.
begin;
create function public.list_source_cleanup() returns table(source_id uuid)
language plpgsql security definer set search_path='' as $$
declare v_owner uuid:=auth.uid();
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  return query select c.source_id from gather_private.cleanup_requests c
    join public.sources s on s.id=c.source_id and s.owner_id=c.owner_id
    where c.owner_id=v_owner and s.deleted_at is not null
    order by c.created_at,c.source_id limit 20;
end $$;

create function public.complete_source_cleanup(p_source uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare v_owner uuid:=auth.uid(); v_deleted timestamptz;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_source is null then return false; end if;
  perform 1 from gather_private.source_quotas where owner_id=v_owner for update;
  select deleted_at into v_deleted from public.sources
    where id=p_source and owner_id=v_owner for update;
  if not found then
    -- Idempotent acknowledgement of this owner's already completed deletion.
    return exists(select 1 from gather_private.save_receipts where owner_id=v_owner and source_id=p_source)
      and not exists(select 1 from public.sources where id=p_source);
  end if;
  if v_deleted is null then return false; end if;
  return gather_private.finish_source_cleanup(p_source);
end $$;
revoke all on function public.list_source_cleanup(),public.complete_source_cleanup(uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function public.list_source_cleanup(),public.complete_source_cleanup(uuid) to authenticated;
commit;
