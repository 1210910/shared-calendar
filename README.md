
# 🎮 Game Night Scheduler (Streamlit)

Simple, good-looking Streamlit app to coordinate gaming availability with friends.
Everyone uses the **same group password** to log in. Data is stored locally in a SQLite database.

## Quick start (local)

```bash
git clone <your-repo-url>
cd game-night-scheduler
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Set the shared password (optional; defaults to "letmein")
export PASSWORD="choose-a-group-password"   # Windows PowerShell: $env:PASSWORD="choose-a-group-password"
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Password options

- **Recommended:** put it in Streamlit secrets when deploying to Streamlit Cloud. Create a file `.streamlit/secrets.toml` with:
  ```toml
  PASSWORD = "choose-a-group-password"
  ```
- **Local dev:** set an environment variable `PASSWORD` before starting the app.
- **Fallback:** if neither is set, the password defaults to `letmein`.

> This is a lightweight gate meant for FRIENDS. It is not meant for production-grade security.

## What gets stored

- A SQLite database file `availability.db` in the project folder.
- Tables:
  - `users(name)`
  - `availability(name, day, slot, available)`

To reset data, delete `availability.db` and restart the app.

## Customizing time slots

Edit `TIME_SLOTS` near the top of `app.py`.

## Project structure

```
game-night-scheduler/
├─ app.py
├─ availability.db           # created at first run
├─ styles.css
├─ requirements.txt
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.toml           # (optional; not committed)
└─ README.md
```

## Deploying to Streamlit Cloud

- Push this folder to a Git repo.
- On Streamlit Cloud, set the app entrypoint to `app.py`.
- Add a secret named `PASSWORD` under **App > Settings > Secrets** (or create `.streamlit/secrets.toml` in the repo, but don't commit real secrets!)

## License

MIT — do whatever, just don't blame me if your friends still can't pick a time 😄
