| Family | TD 1 cells | TD 1 rate (5 models) | First call (cheapest correct) | Dashboard | Customer | Payout | If unavailable |
|---|---|---|---|---|---|---|---|
| F1 period | C01,C04,C05,C06,C07,C20 | 30/30 cells correct (five models) | groq:openai/gpt-oss-20b | none | quorum_2of3 | reference | groq:openai/gpt-oss-120b, groq:qwen/qwen3.8-27b, openrouter:cohere/north-mini-code:free, openrouter:dots-studio/dots-3-note-preview:free, groq-developer:openai/gpt-oss-120b |
| F2 completed age on a reference date | C02,C08,C09,C11 | 12/20 cells correct (five models) | groq:openai/gpt-oss-120b | none | quorum_2of3 | reference | groq:qwen/qwen3.8-27b, groq-developer:openai/gpt-oss-120b |
| F2b age at the time of the order | C10 | 2/5 cells correct (five models) | groq:openai/gpt-oss-20b | reference | reference | reference | groq:openai/gpt-oss-120b, groq-developer:openai/gpt-oss-120b |
| F3 product list | C03,C12,C13,C14 | 19/20 cells correct (five models) | groq:openai/gpt-oss-20b | none | quorum_2of3 | reference | groq:openai/gpt-oss-120b, openrouter:cohere/north-mini-code:free, openrouter:dots-studio/dots-3-note-preview:free, groq-developer:openai/gpt-oss-120b |
| F4 combined filters (period, age, product) | C15,C16,C17,C18,C19 | 17/25 cells correct (five models) | groq:openai/gpt-oss-20b | quorum_3of5 | quorum_3of5 | reference | defer, then billed route, then abstain |
