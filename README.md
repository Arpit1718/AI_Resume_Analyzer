# AI Resume Analyzer

A Flask web app that compares your resume against a target job role and tells you what to improve. Upload a PDF or DOCX (or paste the text), enter the role you want, and get:

- the skills on your resume that fit the role
- the skills you are missing
- a step-by-step learning roadmap to close those gaps
- interview questions to practice

Every analysis is saved to your account, so you can review it later on the History page.

<!-- Add a screenshot or GIF here, e.g. ![Dashboard](screenshots/dashboard.png) -->

**Live demo:** _add your link here once deployed_

## Features

- User accounts with signup, login and logout (passwords are hashed, never stored as plain text)
- Resume input as a PDF, a DOCX, or pasted text
- Role-specific AI analysis returned as structured JSON
- History page with every past analysis, newest first
- Input checks and friendly error messages (unsupported file, unreadable file, empty input, AI failure)
- 5 MB upload limit and secrets kept out of the code through environment variables

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python, Flask |
| Database | SQLAlchemy ORM with TiDB Cloud (MySQL-compatible); SQLite also works locally |
| File parsing | PyPDF2, python-docx |
| AI | Any OpenAI-compatible chat API, used through the `openai` Python SDK |
| Frontend | Jinja2 templates, plain HTML and CSS |

## Project structure

```
Ai_Resume_analyzer/
├── app.py              # Flask routes: signup, login, dashboard, history, logout
├── ai.py               # Builds the prompt, calls the AI API, parses the JSON reply
├── db.py               # Database engine and session setup
├── models.py           # User and Report tables
├── requirements.txt
├── .env.example        # Template for your own .env file
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── _report.html    # Shared layout for showing an analysis
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    └── history.html
```

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the template and fill in your own values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Long random string used to sign session cookies |
| `DATABASE_URL` | SQLAlchemy URL, e.g. `sqlite:///app.db` for local use or a `mysql+pymysql://...` URL |
| `LLM_API_KEY` | API key for your AI provider |
| `LLM_BASE_URL` | OpenAI-compatible endpoint of your provider |
| `LLM_MODEL` | Model name to use |

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Free tiers from providers such as Google AI Studio (Gemini) or Groq work with this setup. Check the provider's docs for the current base URL, model names and rate limits.

### 3. Run

```bash
python app.py
```

Open http://127.0.0.1:5000, create an account and analyze your first resume. The database tables are created automatically on first start.

## How it works

1. The route in `app.py` extracts text from the uploaded PDF or DOCX, or uses the pasted text.
2. `ai.py` sends the resume and the target role to the AI model with a prompt that asks for JSON only.
3. The reply is parsed and checked for the expected keys: `skills`, `missing_skills`, `roadmap`, `interview_questions`.
4. Successful results are saved to the database and shown on the page. Failed requests are logged on the server and are not saved.

## Security notes

- Passwords are hashed with Werkzeug (`generate_password_hash` / `check_password_hash`).
- Secrets and database credentials come from environment variables, and `.env` is excluded from git.
- The resume text is treated as untrusted data in the AI prompt.
- Debug mode is off unless you set `FLASK_DEBUG=1`.

## Limitations

- Scanned PDFs without selectable text can't be read.
- AI output depends on the model and can be wrong, so treat it as guidance.
- Free AI tiers have rate limits, and some providers may use prompts to improve their products. Don't upload other people's resumes.

## Ideas for next steps

- Match score between the resume and a pasted job description
- Suggestions for rewriting weak resume bullet points
- Rate limiting on login
- Delete and download options for saved analyses
- Docker setup and a deployed demo

## License

Add a license of your choice (for example MIT) and mention it here.
