-- iClock production evidence ledger. ADDITIVE: preserves existing tables.
CREATE TABLE IF NOT EXISTS public.i_clock_evidence (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 owner_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 body jsonb NOT NULL,
 sha256 text NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
 created_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT evidence_body_schema CHECK (body->>'schema' = 'iclock-server-evidence/1')
);
CREATE INDEX IF NOT EXISTS i_clock_evidence_owner_created_idx ON public.i_clock_evidence(owner_id,created_at DESC);
ALTER TABLE public.i_clock_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.i_clock_evidence FORCE ROW LEVEL SECURITY;
REVOKE ALL ON public.i_clock_evidence FROM anon, authenticated;
GRANT SELECT, INSERT ON public.i_clock_evidence TO authenticated;
DROP POLICY IF EXISTS clock_owner_select ON public.i_clock_evidence;
CREATE POLICY clock_owner_select ON public.i_clock_evidence FOR SELECT TO authenticated USING ((SELECT auth.uid())=owner_id);
DROP POLICY IF EXISTS clock_owner_insert ON public.i_clock_evidence;
CREATE POLICY clock_owner_insert ON public.i_clock_evidence FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid())=owner_id);
-- No UPDATE or DELETE grants/policies. SHA-256 validates integrity, not authorship.
