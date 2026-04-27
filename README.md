# 🌸 Amma's English Tutor

A warm, personalised English tutor web app built with love for Amma.
Powered by Python + Streamlit + OpenAI.

Because Amma is in India and you're elsewhere, the app is designed to run on
**Streamlit Community Cloud** (free) with **Supabase** (free PostgreSQL) so her
progress is saved permanently — no matter when you redeploy.

---

## Pages

| Page | What it contains |
|---|---|
| 🌸 **Home / Today's Practice** | Daily AI task, Telugu help, example, easier version, feedback |
| 🎯 **More Practice** | Extra tasks — pick a topic or get a surprise |
| 📚 **Words I Learnt** | All vocabulary, searchable, grouped by month |
| 📊 **My Progress** | Encouraging streak, stats, recent sessions |
| 👀 **Likhith's View** | Password-protected parent dashboard + AI weekly summary |

---

## Running locally (VS Code)

### 1. Open the project

`File → Open Folder → English_tutor`

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Mac/Linux
# Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and fill in:
```
OPENAI_API_KEY=sk-your-key-here
PARENT_PASSWORD=choose-a-password
# Leave DATABASE_URL blank locally — it will use SQLite
```

### 5. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Local data is saved in `english_tutor.db`.

---

## Deploying for free (Streamlit Cloud + Supabase)

Since Amma is in India, you need two free cloud services:
1. **Supabase** — stores her progress permanently (free PostgreSQL)
2. **Streamlit Community Cloud** — hosts the app (free)

### Step 1 — Create a free Supabase database

1. Go to [supabase.com](https://supabase.com) → **Start for free** → sign up.
2. Click **New project**, give it a name (e.g. `amma-tutor`), choose a region
   close to India (e.g. **Singapore** or **Mumbai** if available), set a strong password.
3. Wait ~2 minutes for the project to provision.
4. Go to **Project Settings → Database → Connection string → URI**.
5. Copy the URI — it looks like:
   ```
   postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
   Replace `[YOUR-PASSWORD]` with the password you set.
6. Keep this string safe — you'll need it in the next step.

> The Supabase free tier gives 500 MB and up to 50,000 rows — more than enough
> for years of daily practice sessions.

### Step 2 — Push to a private GitHub repo

```bash
git init
git add .
git commit -m "Initial commit"
# Create a new PRIVATE repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/amma-tutor.git
git push -u origin main
```

> `.gitignore` already excludes `.env`, `*.db`, and `secrets.toml` so nothing
> sensitive is committed.

### Step 3 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub.
2. **New app** → choose your repo, branch `main`, main file `app.py`.
3. Click **Advanced settings → Secrets** and paste:

```toml
OPENAI_API_KEY = "sk-your-key-here"
PARENT_PASSWORD = "choose-a-password"
DATABASE_URL = "postgresql://postgres.[ref]:[password]@[host]:5432/postgres"
```

4. Click **Deploy**.

Your app gets a permanent URL like `https://your-app.streamlit.app`.
**Share that URL with Amma** — she can bookmark it on her phone in India.

Her progress is stored in Supabase and survives redeployments, restarts,
and any future changes you make to the code.

---

## Project structure

```
English_tutor/
├── app.py                      ← Home / Today's Practice
├── pages/
│   ├── 1_More_Practice.py
│   ├── 2_Words_Learnt.py
│   ├── 3_My_Progress.py
│   └── 4_Likhiths_View.py
├── modules/
│   ├── database.py             ← SQLite (local) or PostgreSQL (cloud)
│   ├── prompts.py              ← OpenAI prompt builders
│   └── tutor.py                ← OpenAI API calls (gpt-4o-mini)
├── .streamlit/
│   └── config.toml             ← Warm colour theme
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Cost estimate

| Service | Cost |
|---|---|
| Streamlit Community Cloud | **Free** |
| Supabase free tier | **Free** (500 MB, no credit card) |
| OpenAI gpt-4o-mini | ~**$0.001/session** → ~₹3/month for daily use |

---

## Customising

| What to change | Where |
|---|---|
| Amma's name | `app.py` — greeting section |
| Default password | `.env` → `PARENT_PASSWORD` |
| AI model | `modules/tutor.py` → `MODEL = "gpt-4o-mini"` |
| Colour scheme | `.streamlit/config.toml` |
| Task types | `modules/prompts.py` → `build_task_generation_prompt` |
