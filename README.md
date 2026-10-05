# Agentic Grievance NLP Core (Hindi + English MVP)

A working, standalone Python implementation of the "Agentic NLP Engine" block from
your architecture diagram — language detection → translation → category
classification → entity extraction → priority prediction → sentiment analysis →
routing → case storage. Built so it can be wired into a ServiceNow PDI later
via REST, with zero changes to the pipeline logic itself.

## Why it's not in ServiceNow yet
This runs entirely in Python/FastAPI/SQLite so you can build and demo the hard
NLP part immediately. When you get a ServiceNow PDI, you point ServiceNow's
IntegrationHub/Flow Designer at `POST /grievance` on this service (or move the
`Case` write from `app/database.py` into a ServiceNow Table API call) — the six
NLP modules don't change at all.

## Project layout
```
app/
  config.py            # model names, categories, department map, urgency keywords
  database.py           # SQLite "Case" table (stand-in for ServiceNow CSM)
  routing.py             # category -> department rules (stand-in for Assignment Rules)
  main.py                 # FastAPI endpoints
  pipeline/
    language_detect.py   # Step 1
    translate.py           # Step 2 (Hindi -> English, IndicTrans2)
    classify.py             # Step 3 (zero-shot category classification)
    ner.py                   # Step 4 (entity extraction)
    priority.py               # Step 5 (rule-based urgency scoring)
    sentiment.py                # Step 6
    orchestrator.py              # chains all six steps into one case record
dashboard/
  dashboard.py           # Streamlit "Government Dashboard" stand-in
tests/
  sample_grievances.py    # 5 sample Hindi/English grievances to sanity-test
```

## A note on the translation module
`app/pipeline/translate.py` does NOT depend on the `IndicTransToolkit` package.
That package ships a Cython extension that needs a C++ compiler to build on
Windows (Microsoft Visual C++ Build Tools), which is a common source of
install failures. Instead, the small amount of pre/post-processing IndicTrans2
needs (normalize → tokenize → tag with `hin_Deva`/`eng_Latn` → detokenize) is
reimplemented directly using `indic-nlp-library-itt` and `sacremoses`, both
pure-Python packages that install with plain `pip` on any OS, no compiler
required. The actual translation model (`ai4bharat/indictrans2-indic-en-dist-200M`)
is unchanged — only the surrounding glue code is different.

## Setup (run this locally, NOT in a network-restricted sandbox — it needs
## to download several models from Hugging Face on first run)

```bash
cd grievance-nlp-core
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

First run will download ~2-3 GB of model weights (IndicTrans2, mDeBERTa,
IndicNER, sentiment models). This only happens once; models are cached locally.

## Run it

**1. Quick sanity test (no server needed):**
```bash
python tests/sample_grievances.py
```
This runs the 5 sample grievances end-to-end and prints every field the
pipeline extracts, so you can confirm each model is working before wiring up
the API.

**2. Start the API:**
```bash
uvicorn app.main:app --reload
```
Then POST a grievance:
```bash
curl -X POST http://localhost:8000/grievance \
  -H "Content-Type: application/json" \
  -d '{"text": "मेरी गली में पिछले 5 दिनों से पानी की आपूर्ति नहीं है।"}'
```
Interactive API docs: http://localhost:8000/docs

**3. Start the dashboard (separate terminal, API must be running):**
```bash
streamlit run dashboard/dashboard.py
```

## Build order (maps to your CA-3 sprint plan, scoped to this Python core)

| Order | What to build | Notes |
|---|---|---|
| 1 | Run `tests/sample_grievances.py`, confirm all 6 models load & produce sane output | Do this first — most setup pain (downloads, `trust_remote_code`, GPU/CPU) surfaces here |
| 2 | Wrap with FastAPI (`app/main.py`) — already done | Test via `/docs` |
| 3 | Collect 50-100 REAL Hindi + English sample grievances (scrape sample civic complaint text, or write synthetic ones per category) | Needed for step 4 and for your evaluation section (CA-3 §4.1 metrics) |
| 4 | Fine-tune MuRIL on your labeled data, swap into `classify.py` behind the same function signature, compare accuracy against the zero-shot baseline | This is your "hybrid classification strategy" deliverable |
| 5 | Build the Streamlit dashboard out further: SLA compliance %, language-wise distribution, resolution-time trends | Matches "Analytics & Dashboards" block |
| 6 | Add a `/cases/{id}/status` webhook + simple SLA timer (flag cases open > N hours as breached) | Stand-in for SLA Management block |
| 7 | Get ServiceNow PDI, recreate the Case table as a Custom Table or extend `sn_customerservice_case`, add a Flow that calls `POST /grievance` on Case creation | This is where the two halves merge |
| 8 | Replace the Python `Case` writes with ServiceNow Table API calls | At this point the NLP core becomes a pure microservice ServiceNow calls |

## NEW: Audio grievances (voice complaints)
Citizens can now submit a complaint as an audio file instead of typing.
- **New model:** `openai/whisper-small` transcribes speech to text (Hindi or
  English, auto-detected) via `app/pipeline/speech_to_text.py`. This is the
  ONLY new AI model — once transcribed, the text re-enters the exact same
  6-stage pipeline used for typed grievances, completely unchanged.
- **New endpoint:** `POST /grievance/audio` — accepts an uploaded audio file
  (`multipart/form-data`, field name `audio`), transcribes it, runs the normal
  pipeline, and saves the case exactly like `POST /grievance` does.
- **New field:** every case now has a `source` column (`"text"` or `"voice"`)
  so you can tell which channel a grievance came in through.
- **New citizen portal option:** an audio file upload button sits below the
  text form in `citizen-portal.html`.

### Required: install ffmpeg (one-time, system-level, NOT a pip package)
Whisper needs `ffmpeg` installed on your system PATH to decode whatever audio
format gets uploaded (mp3, m4a, wav, webm, etc.). Unlike the earlier Visual
C++ Build Tools issue, this does NOT require a compiler — it's just adding one
program to your PATH.

**Windows — easiest method (if you have `winget`, built into Windows 10/11):**
```
winget install ffmpeg
```
Then close and reopen your terminal.

**Windows — manual method (if winget isn't available):**
1. Download a build from https://www.gyan.dev/ffmpeg/builds/ (get the
   "release essentials" zip)
2. Extract it somewhere permanent, e.g. `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH: search "Environment Variables" in the
   Start menu → Edit the "Path" variable under your user variables → New →
   paste `C:\ffmpeg\bin`
4. Close and reopen your terminal, then verify with `ffmpeg -version`

**Mac:** `brew install ffmpeg`
**Linux:** `sudo apt install ffmpeg` (Ubuntu/Debian) or your distro's equivalent

### Important: your existing database needs to be recreated
Adding the `source` column changes the database schema. Your existing
`grievances.db` (created before this update) won't have that column and will
error. **Delete `grievances.db`** in your project root before restarting
`uvicorn` — it will recreate itself automatically, empty, with the new schema
on the next startup. (This means you'll lose your existing test cases — if you
want to keep a record of them first, take a screenshot of the dashboard.)

### Try it
```bash
curl -X POST http://localhost:8000/grievance/audio \
  -F "audio=@/path/to/your/recording.mp3"
```
Or use the audio upload button in `citizen-portal.html`, or test via
`http://localhost:8000/docs` (the `POST /grievance/audio` endpoint there has
a file-picker built in).

## NEW: Image grievances (photo-based complaints)
Citizens can now submit a complaint as a photo instead of text or audio.
- **New model:** `openai/clip-vit-base-patch32` (CLIP) — a vision-language
  model that compares a photo against text descriptions and picks the best
  match, via `app/pipeline/image_classify.py`. Same zero-shot philosophy as
  the text classifier, just for images; CLIP genuinely needs full-sentence
  prompts ("a photo of...") rather than the short labels the text classifier
  uses — a different model, different expected prompting style.
- **Two passes per image:** one against category descriptions (Water, Roads,
  Electricity, etc.), one against severity descriptions (dangerous / moderate
  / minor), producing both a category and a rough priority — **this priority
  signal is meaningfully less reliable than the text/voice priority engine**,
  since there's no text to corroborate it. Disclose this if asked.
- **New endpoint:** `POST /grievance/image` — accepts an uploaded photo
  (`multipart/form-data`, field name `image`) plus an optional short text
  `description`, classifies it, and creates a case exactly like the other
  two endpoints.
- **Photos are saved** to `uploaded_images/` and served back out at
  `http://localhost:8000/images/<filename>` so the dashboard and citizen
  portal can actually display them, not just reference a filename.
- **New field:** `source` can now be `"text"`, `"voice"`, or `"image"`.
- Citizen portal: a third submission option ("Have a photo of the problem?")
  below the text and voice options, with a live thumbnail preview before
  submitting. The tracker shows the photo alongside the grievance details.
- Dashboard: the case preview shows the attached photo directly when
  present, plus a source label (Typed / Voice recording / Photo).

## Model reference (Hindi + English only, per current project scope)

| Step | Model | HF link |
|---|---|---|
| Language detection | `papluca/xlm-roberta-base-language-detection` | huggingface.co/papluca/xlm-roberta-base-language-detection |
| Translation (hi→en) | `ai4bharat/indictrans2-indic-en-dist-200M` | huggingface.co/ai4bharat/indictrans2-indic-en-dist-200M |
| Category classification | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` (zero-shot) → later fine-tuned `google/muril-base-cased` | huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli |
| Entity extraction (Hindi) | `cfilt/HiNER-original-muril-base-cased` | huggingface.co/cfilt/HiNER-original-muril-base-cased |
| Entity extraction (English) | `dslim/bert-base-NER` | huggingface.co/dslim/bert-base-NER |
| Sentiment (Hindi + English) | `cardiffnlp/twitter-xlm-roberta-base-sentiment` | huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment |
| Priority scoring | Rule-based (see `app/pipeline/priority.py`) | no pretrained model exists for this |
| **Speech-to-text (NEW)** | `openai/whisper-small` | huggingface.co/openai/whisper-small |

## Known limitations to disclose in your report
- Category classification is zero-shot until you fine-tune on real labeled data — expect it to be noticeably less accurate than a supervised model, which is exactly the comparison your CA-3 evaluation table (§4.1) asks for.
- Priority scoring is a transparent rule engine, not ML — this is intentional and matches your methodology's stated upgrade path (regression model once resolution-time data exists).
- Only Hindi + English are wired up; other Indic languages fall back to the English pipeline until you add per-language model routing (same pattern as `ner.py`/`sentiment.py`).
- Audio transcription quality depends on recording clarity and background noise; Whisper's language auto-detection can occasionally mislabel very short or noisy clips.
