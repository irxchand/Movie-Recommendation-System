from gpt4all import GPT4All
import requests
import os
import re
import difflib
from datetime import datetime


TMDB_API_KEY = # Write your own api key here.


MAPPINGS_DIR = r"E:/GP4ALL/Local Docs"
ACTORS_FILE = os.path.join(MAPPINGS_DIR, "actors.txt")
GENRES_FILE = os.path.join(MAPPINGS_DIR, "genre.txt")
LANGUAGES_FILE = os.path.join(MAPPINGS_DIR, "languages.txt")

MODEL_PATH = r"E:/GP4ALL/Models/Phi-3-mini-4k-instruct.Q4_0.gguf"


def load_mapping(filepath):
    mapping = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, val = line.strip().split(":", 1)
                mapping[key.strip().lower()] = val.strip()
    return mapping

ACTOR_MAP = load_mapping(ACTORS_FILE)
GENRE_MAP = load_mapping(GENRES_FILE)
LANGUAGE_MAP = load_mapping(LANGUAGES_FILE)


def fuzzy_choice(token, mapping_keys, cutoff=0.6):

    choices = difflib.get_close_matches(token, mapping_keys, n=1, cutoff=cutoff)
    return choices[0] if choices else None


def expanded_dates_from_text(text):
   
    text = text.lower()
    
    m = re.search(r'((?:19|20)\d{2})\s*[-to]+\s*((?:19|20)\d{2})', text)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        return f"{y1:04d}-01-01", f"{y2:04d}-12-31"

    
    m = re.search(r'((?:19|20)\d)0s', text)
    if m:
        decade = int(m.group(1)) * 10
        return f"{decade}-01-01", f"{decade+9}-12-31"


    m = re.search(r'(early|mid|late)\s+((?:19|20)\d{2})s', text)
    if m:
        part, decade_start = m.group(1), int(m.group(2)) * 10
        if part == "early":
            return f"{decade_start}-01-01", f"{decade_start+4}-12-31"
        if part == "mid":
            return f"{decade_start+4}-01-01", f"{decade_start+6}-12-31"
        if part == "late":
            return f"{decade_start+6}-01-01", f"{decade_start+9}-12-31"

  
    m = re.search(r'\b((?:19|20)\d{2})\b', text)
    if m:
        y = int(m.group(1))
        return f"{y:04d}-01-01", f"{y:04d}-12-31"

    return None, None


def local_infer_from_text(text):
 
    out = {}
    t = text.lower()

   
    sorted_actors = sorted(ACTOR_MAP.keys(), key=lambda x: -len(x))
    for actor_key in sorted_actors:
        if actor_key in t:
            out["actor_id"] = ACTOR_MAP[actor_key]
            break


    sorted_genres = sorted(GENRE_MAP.keys(), key=lambda x: -len(x))
    for g in sorted_genres:
        if g in t:
            out["genre_id"] = GENRE_MAP[g]
            break


    for lang in LANGUAGE_MAP.keys():
        if lang in t:
            out["language"] = LANGUAGE_MAP[lang]
            break

  
    if "actor_id" not in out:
  
        tokens = re.findall(r"[a-zA-Z]+(?:\s+[a-zA-Z]+)?", t)
        keys = list(ACTOR_MAP.keys())
        for tok in tokens:

            cand = fuzzy_choice(tok.strip(), keys, cutoff=0.82)
            if cand:
                out["actor_id"] = ACTOR_MAP[cand]
                break
            last = tok.strip().split()[-1]
            cand = fuzzy_choice(last, keys, cutoff=0.9)
            if cand:
                out["actor_id"] = ACTOR_MAP[cand]
                break


    if "genre_id" not in out:
        tokens = re.findall(r"[a-zA-Z]+", t)
        keys = list(GENRE_MAP.keys())
        for tok in tokens:
            cand = fuzzy_choice(tok, keys, cutoff=0.8)
            if cand:
                out["genre_id"] = GENRE_MAP[cand]
                break

    d1, d2 = expanded_dates_from_text(t)
    if d1 and d2:
        out["date_from"] = d1
        out["date_to"] = d2

    return out

def parse_assignments(text):
 
    results = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(ACTOR_ID|GENRE_ID|LANGUAGE|DATE_FROM|DATE_TO)\s*=\s*["\']?(.*?)["\']?\s*$', line)
        if m:
            key, val = m.group(1), m.group(2)
            if key == "ACTOR_ID":
                results["actor_id"] = val
            elif key == "GENRE_ID":
                results["genre_id"] = val
            elif key == "LANGUAGE":
                results["language"] = val
            elif key == "DATE_FROM":
                results["date_from"] = val
            elif key == "DATE_TO":
                results["date_to"] = val
    return results

SYSTEM_PROMPT_TEMPLATE = """
You are KRK.
Your only job is to convert your understanding of the user's movie preference
into Python variable assignments. You can also chat with the user.
Allowed variables:
ACTOR_ID
GENRE_ID
LANGUAGE
DATE_FROM
DATE_TO
Output ONLY lines like:
ACTOR_ID = "35070"
GENRE_ID = "28"
LANGUAGE = "hi"
DATE_FROM = "2000-01-01"
DATE_TO = "2010-12-31"
"""

mapping_injection = {
    "actors": "\n".join(f"{k}: {v}" for k, v in ACTOR_MAP.items()),
    "genres": "\n".join(f"{k}: {v}" for k, v in GENRE_MAP.items()),
    "languages": "\n".join(f"{k}: {v}" for k, v in LANGUAGE_MAP.items()),
}

SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(**mapping_injection)

model = GPT4All(MODEL_PATH)


ACTOR_ID = ""
GENRE_ID = ""
LANGUAGE = "en"
DATE_FROM = "2000-01-01"
DATE_TO = "2025-12-31"

print("KRK ready. Type natural language preferences. Type 'recommend' to fetch movies. 'exit' to quit.")
name = input("Enter your name: ")

while True:
    user = input(f"{name}: ").strip()
    if not user:
        continue
    if user.lower() in ["exit", "quit"]:
        print("KRK: Goodbye.")
        break

    if user.lower() == "recommend":
        print("KRK: querying TMDb...\n")
        url = (
            f"https://api.themoviedb.org/3/discover/movie?"
            f"api_key={TMDB_API_KEY}"
            f"&with_original_language={LANGUAGE}"
            f"&with_cast={ACTOR_ID}"
            f"&with_genres={GENRE_ID}"
            f"&primary_release_date.gte={DATE_FROM}"
            f"&primary_release_date.lte={DATE_TO}"
            f"&sort_by=popularity.desc&page=1"
        )
        resp = requests.get(url)
        try:
            data = resp.json()
        except Exception as e:
            print("KRK: TMDb error:", e)
            continue
        movies = data.get("results", [])[:5]
        if not movies:
            print("KRK: No results found with current preferences.\n")
        else:
            for i, m in enumerate(movies, 1):
                title = m.get("title", "N/A")
                year = (m.get("release_date") or "")[:4]
                score = m.get("vote_average")
                print(f"{i}. {title} ({year}) - score: {score}")
        continue

    inferred = local_infer_from_text(user)

    
    need_model = False
    
    for key in ("actor_id", "genre_id", "language", "date_from", "date_to"):
        if key not in inferred:
            need_model = True
            break

    model_output = ""
    if need_model:
       
        extraction_prompt = SYSTEM_PROMPT + "\nUser: " + user + "\nKRK:"
       
        model_output = model.generate(extraction_prompt, max_tokens=200)
        print("\n[KRK internal]:\n" + model_output + "\n")
        parsed = parse_assignments(model_output)
    else:
        parsed = {}

    final = {}
    final["actor_id"] = parsed.get("actor_id", inferred.get("actor_id", ""))
    final["genre_id"] = parsed.get("genre_id", inferred.get("genre_id", ""))
    final["language"] = parsed.get("language", inferred.get("language", LANGUAGE))
    final["date_from"] = parsed.get("date_from", inferred.get("date_from", DATE_FROM))
    final["date_to"] = parsed.get("date_to", inferred.get("date_to", DATE_TO))

    
    if final["actor_id"]:
        ACTOR_ID = final["actor_id"]
    if final["genre_id"]:
        GENRE_ID = final["genre_id"]
    if final["language"]:
        LANGUAGE = final["language"]
    if final["date_from"]:
        DATE_FROM = final["date_from"]
    if final["date_to"]:
        DATE_TO = final["date_to"]

    print("KRK: Preferences updated:")
    print(f"  ACTOR_ID = {ACTOR_ID}")
    print(f"  GENRE_ID = {GENRE_ID}")
    print(f"  LANGUAGE = {LANGUAGE}")
    print(f"  DATE_FROM = {DATE_FROM}")
    print(f"  DATE_TO = {DATE_TO}\n")

