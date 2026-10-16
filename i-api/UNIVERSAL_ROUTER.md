# iUniversalApi Router — Render deployment
Service: https://i-the-one-buddy-api.onrender.com
Routes: GET /v1/universal/providers, POST /v1/universal/chat (authenticated), POST /v1/actions (authenticated, signed/persisted if configured).

Render environment variables: provider token/key AND real served model ID are required.
OpenAI: IAPI_OPENAI_KEY, IAPI_OPENAI_MODEL_ID
Anthropic: IAPI_ANTHROPIC_KEY, IAPI_ANTHROPIC_MODEL_ID
Groq: IAPI_GROQ_KEY, IAPI_GROQ_MODEL_ID
DeepSeek: IAPI_DEEPSEEK_KEY, IAPI_DEEPSEEK_MODEL_ID
Google Gemini compatible: IAPI_GOOGLE_KEY, IAPI_GOOGLE_MODEL_ID
Hugging Face: IAPI_HF_TOKEN, IAPI_HF_MODEL_ID
MIT-licensed self-hosted: IAPI_MIT_BASE_URL, IAPI_MIT_API_KEY, IAPI_MIT_MODEL_ID
Apache-2.0 self-hosted: IAPI_APACHE2_BASE_URL, IAPI_APACHE2_API_KEY, IAPI_APACHE2_MODEL_ID

MIT and Apache 2.0 are licenses, NOT inference providers. Host the actual legally compatible model yourself with OpenAI-compatible HTTPS serving.
ChatGPT Hugging Face OAuth does not automatically make tokens available to the Render application.
Configured status checks merely show environment presence, not successful inference.
Provider passwords never belong in GitHub or the public PWA config.
Request a signed persisted action receipt only after Supabase JWT auth, storage/RLS, and an Ed25519 signing key are configured.
Do not merge protected branches without review and explicit approval.