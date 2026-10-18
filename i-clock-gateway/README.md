# iClock authenticated evidence gateway — deployment candidate

This is a Node.js service and an additive Supabase PostgreSQL RLS migration, with no production npm dependencies. Browser time precision is not certified. Events are hashed and persisted via an authenticated user's bearer session; a database write acknowledgment is required before HTTP 201. No hardware PUF claims.

## Run
Use Node.js 20+: `npm test`, `npm start`. The deployment environment must provide `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and optionally `PORT`. Apply `deploy/iclock_rls.sql` to a backed-up, active Supabase project after reviewing access policies. Never expose server tokens or execution shells in browser code.

## Release gates
Supabase BUDDY project tkrxmdonmxpeockpbazl is reported INACTIVE (October 18, 2026), so no production writes have been verified. This change is intentionally review-only. A separate Render Node web service with HTTPS and restricted CORS, abuse limits, deployment variables, end-to-end auth/persistence tests, and security review is required before release. Existing Render static site cannot execute this service. No database migration has been executed.