# Anthropic profile

Recommended transport: direct `anthropic` provider.

Typical setup:
- provider: `anthropic`
- base URL: `https://api.anthropic.com` or proxy
- API key env: `ANTHROPIC_API_KEY`
- model: Claude Messages API model id

Operational note:
Audit-Proof currently treats Anthropic as a JSON-returning evidence engine and parses the returned text blocks conservatively.
