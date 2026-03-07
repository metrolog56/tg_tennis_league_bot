-- Allow Realtime to broadcast changes on matches (for instant UI updates when opponent submits result).
do $$
begin
  if not exists (
    select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'matches'
  ) then
    alter publication supabase_realtime add table matches;
  end if;
end $$;
