-- Free enrollment while payments are off, and the write policies it replaces.
-- Example schema (courses, purchases); rename to the app's own tables.
--
-- A closed test where every paid item shows "coming soon" gets testers who
-- never reach the product, so enroll_free_course grants it at amount 0.
--
-- The policies dropped below are the reason this is a function and not a plain
-- client insert. "Users can insert own purchases" checked only that the row
-- belonged to the caller - not the amount, not the status, not whether money
-- moved. Anyone holding the anon key could grant themselves any paid course
-- with one REST call, without the app. Granting entitlement is a server
-- decision, so both write policies go and this function becomes the only way in.
-- Paid enrolment gets its own path: the server verifies the payment provider's
-- signature and writes with the service role.

DROP POLICY IF EXISTS "Users can insert own purchases" ON public.purchases;
DROP POLICY IF EXISTS "Users can update own purchases" ON public.purchases;

CREATE OR REPLACE FUNCTION public.enroll_free_course(p_course_id uuid)
RETURNS public.purchases
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_purchase public.purchases;
BEGIN
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'not authenticated' USING ERRCODE = '28000';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM public.courses WHERE id = p_course_id AND is_active
  ) THEN
    RAISE EXCEPTION 'course not available' USING ERRCODE = '22023';
  END IF;

  INSERT INTO public.purchases (user_id, course_id, amount, status)
  VALUES (auth.uid(), p_course_id, 0, 'completed')
  ON CONFLICT (user_id, course_id) DO NOTHING
  RETURNING * INTO v_purchase;

  -- Already enrolled. Hand back the existing row rather than failing, so a
  -- double tap on a slow connection is not an error the user has to read.
  -- Deliberately no status update here: a real paid row must never be
  -- rewritten by this path.
  IF v_purchase IS NULL THEN
    SELECT * INTO v_purchase
    FROM public.purchases
    WHERE user_id = auth.uid() AND course_id = p_course_id;
  END IF;

  RETURN v_purchase;
END;
$$;

REVOKE ALL ON FUNCTION public.enroll_free_course(uuid) FROM public;
REVOKE ALL ON FUNCTION public.enroll_free_course(uuid) FROM anon;
GRANT EXECUTE ON FUNCTION public.enroll_free_course(uuid) TO authenticated;
