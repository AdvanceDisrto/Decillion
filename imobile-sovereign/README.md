# iMobile Sovereign Identity + Call Records (development starter)

Replacement architecture: Keycloak (OIDC) + ASP.NET Core API + PostgreSQL. Does not change or remove existing Supabase endpoints; migration must be separately validated before switching clients.

Run `cp .env.example .env`, choose unique local passwords, and run `docker compose --env-file .env up --build`. Configure the `imobile` Keycloak realm and mobile/web OIDC clients manually; do not treat the development Keycloak admin account as a user login. JWT issuer/audience are required for the API to start. Expose only HTTPS through a protected reverse proxy for any external use. No public production deployment in this scaffold.

GET `/health` confirms the API process; GET `/v1/me` requires valid OIDC JWT; GET and POST `/v1/calls` require authentication. Records are scoped by token subject. Only call metadata is stored; voice/video require existing WebRTC + real signaling infrastructure. Provision PostgreSQL schema from `schema.sql` before starting API. Add migrations, token flow tests, APNs/FCM, TURN and durable signaling before production.

No secrets belong in source control. No default administrator password or authentication bypass is provided.
