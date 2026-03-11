-- Constraints and helpers to reduce risk of partially processed matches.
-- This file is not applied automatically; run it manually via Supabase or psql.

-- 1) Forbid equal set scores for matches marked as played.
ALTER TABLE public.matches
ADD CONSTRAINT matches_played_sets_not_equal
CHECK (
  status <> 'played'
  OR sets_player1 IS NOT NULL
  OR sets_player2 IS NOT NULL
  OR sets_player1 <> sets_player2
);

-- 2) (Optional, enable manually) helper function + trigger to log
--    direct status changes to 'played' outside the canonical path.
--    The trigger only records suspicious updates into a helper table;
--    it does NOT block writes by default.

CREATE TABLE IF NOT EXISTS public.inconsistent_matches_log (
  id bigserial PRIMARY KEY,
  match_id uuid NOT NULL,
  old_status text,
  new_status text,
  logged_at timestamptz DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.log_matches_status_played()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'UPDATE'
     AND NEW.status = 'played'
     AND (OLD.status IS DISTINCT FROM NEW.status) THEN
    INSERT INTO public.inconsistent_matches_log (match_id, old_status, new_status)
    VALUES (NEW.id, OLD.status::text, NEW.status::text);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_log_matches_status_played ON public.matches;
CREATE TRIGGER trg_log_matches_status_played
AFTER UPDATE OF status ON public.matches
FOR EACH ROW
EXECUTE FUNCTION public.log_matches_status_played();

