begin;

-- An operator configures the limits before enabling trial mode. A missing
-- policy denies model work. Keep only the current counters and no request data.
create table gather_private.trial_model_policy (
  singleton boolean primary key default true check (singleton),
  daily_account_limit integer not null check (daily_account_limit between 1 and 10000),
  monthly_service_limit integer not null check (monthly_service_limit between 1 and 1000000),
  usage_month date,
  used integer not null default 0 check (used between 0 and 1000000)
);

create table gather_private.trial_model_accounts (
  owner_id uuid primary key references auth.users(id) on delete cascade,
  usage_date date not null,
  used integer not null check (used between 1 and 10000)
);

revoke all on gather_private.trial_model_policy, gather_private.trial_model_accounts
  from public, anon, authenticated, gather_ingestion_coordinator, gather_ingestion_worker;

create function gather_private.trial_model_usage(p_owner uuid, p_charge boolean)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
  policy gather_private.trial_model_policy%rowtype;
  today date;
  month_start date;
  account_used integer;
  service_used integer;
  result_state text;
begin
  if p_owner is null or p_charge is null then
    raise exception 'invalid_trial_usage' using errcode='22023';
  end if;

  -- Both quotas are checked and charged in the same transaction. Serialize
  -- reservations across workers and API instances on this one policy row.
  select * into policy from gather_private.trial_model_policy where singleton for update;
  if not found then return null; end if;
  today := (clock_timestamp() at time zone 'UTC')::date;
  month_start := date_trunc('month', today::timestamp)::date;
  select used into account_used from gather_private.trial_model_accounts
    where owner_id=p_owner and usage_date=today;
  account_used := coalesce(account_used, 0);
  service_used := case when policy.usage_month=month_start then policy.used else 0 end;

  if account_used >= policy.daily_account_limit then
    result_state := 'trial_quota_exhausted';
  elsif service_used >= policy.monthly_service_limit then
    result_state := 'trial_capacity_exhausted';
  else
    result_state := 'available';
    if p_charge then
      account_used := account_used + 1;
      insert into gather_private.trial_model_accounts values (p_owner, today, account_used)
        on conflict (owner_id) do update set usage_date=excluded.usage_date, used=excluded.used;
      update gather_private.trial_model_policy set usage_month=month_start, used=service_used+1
        where singleton;
    end if;
  end if;
  return jsonb_build_object('state',result_state,'used',least(account_used,policy.daily_account_limit),
    'limit',policy.daily_account_limit);
end $$;

create function gather_private.trial_query_usage(p_charge boolean)
returns jsonb language sql security definer set search_path='' as $$
  select gather_private.trial_model_usage(auth.uid(), p_charge)
$$;

create function gather_private.charge_trial_document(p_job uuid, p_token uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
  job gather_private.ingestion_jobs;
  result jsonb;
begin
  job := gather_private.lock_live_job(p_job, p_token);
  result := gather_private.trial_model_usage(job.owner_id, true);
  if job.lease_expires_at <= clock_timestamp() then
    raise exception 'stale_lease' using errcode='55000';
  end if;
  return result;
end $$;

revoke all on function gather_private.trial_model_usage(uuid,boolean),
  gather_private.trial_query_usage(boolean), gather_private.charge_trial_document(uuid,uuid)
  from public, anon, authenticated, gather_ingestion_coordinator, gather_ingestion_worker;
grant execute on function gather_private.trial_query_usage(boolean) to gather_ingestion_coordinator;
grant execute on function gather_private.charge_trial_document(uuid,uuid) to gather_ingestion_worker;

commit;
