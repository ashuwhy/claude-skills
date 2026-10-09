-- Column grants on profiles, so the role an auth gate trusts cannot be set by
-- the user it gates. Example columns; list the app's own.
--
-- A row policy like "Users can update own profile" USING (auth.uid() = id)
-- decides which rows a user may touch, never which columns. Add a role column
-- later and every signed-in user can promote themselves with one REST call,
-- no app needed:
--   PATCH /rest/v1/profiles?id=eq.<own id>   {"role":"admin"}
-- Postgres checks column privileges before RLS, so taking role away from the
-- API roles closes this whatever the policies say.
--
-- Fails closed: table-wide INSERT and UPDATE are revoked (which also revokes
-- every column grant) and only the user-editable columns are granted back. A
-- column added later stays read-only to users until it is listed here, which
-- is the safe way round for the next privileged column too.
--
-- Role changes go through the service role or the SQL editor. If a trigger on
-- auth.users creates the profile row, drop the INSERT grant as well.

REVOKE INSERT, UPDATE ON public.profiles FROM anon, authenticated;

GRANT INSERT (id, full_name, avatar_url) ON public.profiles TO authenticated;
GRANT UPDATE (full_name, avatar_url) ON public.profiles TO authenticated;

-- Verify. Both must be false:
--   SELECT has_column_privilege('authenticated', 'public.profiles', 'role', 'UPDATE'),
--          has_column_privilege('authenticated', 'public.profiles', 'role', 'INSERT');
-- End to end, with a non-admin user's access token, the PATCH above must come
-- back 403 with code 42501. A 200 or 204 means the gate is still open.
