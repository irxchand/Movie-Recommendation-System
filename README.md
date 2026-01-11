# KRK - Local LLM-Driven Movie Recommendation Engine (TMDb)

KRK is a **local-first, deterministic movie recommendation system** that converts **natural language preferences** into **structured TMDb discovery queries**.

It prioritizes **rule-based extraction** and falls back to a **locally hosted LLM (GPT4All + Phi-3)** only when required.

No cloud inference. No black-box behavior.

---

## Design Principles

- **Local inference only** — no OpenAI or external LLM APIs  
- **Rules before AI** — regex, mappings, fuzzy matching first  
- **Strict output contracts** — LLM outputs only variable assignments  
- **Stateful preferences** — preferences persist across turns  
- **Auditable logic** — every decision path is inspectable  

---

## Features

- Natural language preference parsing  
- Actor, genre, language, and date range extraction  
- Decade and period expansion (`90s`, `early 2000s`, `2010–2015`)  
- Fuzzy matching for misspellings  
- Local LLM fallback when deterministic parsing fails  
- TMDb `discover/movie` integration  
- Zero cloud dependency for inference  

---

## Architecture Overview

```
User Input
│
├─ Rule-Based Parsing (regex / substring)
│
├─ Fuzzy Matching (difflib)
│
├─ Date Expansion Logic
│
├─► If incomplete:
│ Local LLM (GPT4All / Phi-3)
│ └─ Strict variable extraction
│
└─ TMDb Discover API
└─ Ranked movie results

```

---

## Tech Stack

- Python 3.9+
- GPT4All
- Phi-3-mini-4k-instruct (Q4_0)
- TMDb API
- requests, re, difflib

---

## Project Structure

```

├── main.py
├── README.md
├── Local Docs/
│ ├── actors.txt
│ ├── genre.txt
│ └── languages.txt
└── Models/
└── Phi-3-mini-4k-instruct.Q4_0.gguf

```

---

## Mapping Files

All mappings use a simple key–value format:

### actors.txt

```
tom cruise: 500
leonardo dicaprio: 6193

```

### genre.txt

```

action: 28
thriller: 53

```

---

### languages.txt

```
english: en
hindi: hi
```

---

- Case-insensitive
- Longest-match priority
- Fuzzy matching enabled

---

## Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/krk-movie-recommender.git
cd krk-movie-recommender
```

```
pip install gpt4all requests
```
---
## Place the model file at

```
E:/GP4ALL/Models/Phi-3-mini-4k-instruct.Q4_0.gguf
```
## TMDb API Key

Create an API key at https://www.themoviedb.org

Set it in main.py:

```
TMDB_API_KEY = "YOUR_API_KEY"
```

---

## Known Limitations

Single actor and genre only

Movies only (no TV shows)

Popularity-based ranking

No user watch history

---

## Future Enhancements

Multi-actor / multi-genre support

Vector re-ranking

Watch history memory

Offline TMDb caching

Modular refactor

---
