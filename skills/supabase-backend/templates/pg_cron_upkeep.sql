-- pg_cron writes one row to cron.job_run_details per run and never prunes it.
-- With process-notifications-every-minute firing 1440x/day, that table reached
-- 196k rows / 134 MB (91% of the database) and exhausted the project's Disk IO
-- budget, which took Postgres offline. Keep three days of run history.

select cron.schedule(
  'purge-cron-run-details',
  '15 3 * * *',
  $$delete from cron.job_run_details where end_time < now() - interval '3 days'$$
);
-- process-notifications-every-minute fired 1440 times a day and is not currently
-- needed. Paused rather than unscheduled so the job definition survives and can be
-- re-enabled with: select cron.alter_job(jobid, active := true).

do $$
declare
  v_jobid bigint;
begin
  select jobid into v_jobid
  from cron.job
  where jobname = 'process-notifications-every-minute';

  if v_jobid is not null then
    perform cron.alter_job(v_jobid, active := false);
  end if;
end
$$;
