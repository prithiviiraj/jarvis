# Groq, not Grok
The owner corrected the intended provider to Groq. Default planned list is LM Studio, Gemini, NIM and Groq. xAI Grok stays an optional legacy preset, not enabled or selected.

Verified official OpenAI-compatible base URL: https://api.groq.com/openai/v1 . Source: https://console.groq.com/docs/openai . No Groq SDK needed for existing bounded HTTP/SSE transport.

Free-tier only. Official billing docs distinguish Free and paid Developer tier: https://console.groq.com/docs/billing-faqs . Adding a key does NOT prove its organization is free. Groq preset is blocked unless the application has verified Free-tier status for the account; cloud disclosure consent and key presence are still separate gates. This verification cannot be guessed from rate limits. No billing upgrade, payment method or paid provider call was performed.

Rate limits vary by model/organization: https://console.groq.com/docs/rate-limits . Do not promise unlimited or guarantee a particular quota. Model selection remains editable. No live Groq request has been run; fake transport tests and localhost SSE prove mechanics, not availability or actual account plan. First real request needs current account/plan proof and user-enabled cloud consent.
