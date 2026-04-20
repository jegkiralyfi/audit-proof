# Gemini profile

Recommended transports:
- direct `gemini` provider for `generateContent`
- or `openai-compatible` when using the Gemini OpenAI compatibility layer

Typical direct setup:
- provider: `gemini`
- base URL: `https://generativelanguage.googleapis.com/v1beta` or proxy
- API key env: `GEMINI_API_KEY`
- model: Gemini model id, with or without `models/` prefix

Operational note:
Audit-Proof requests structured JSON output and still validates the final payload in application code.
