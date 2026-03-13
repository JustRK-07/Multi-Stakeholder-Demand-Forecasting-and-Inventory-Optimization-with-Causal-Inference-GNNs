## RetailCast backend (scaffold)

This folder contains a minimal FastAPI backend that serves stub responses for the existing frontend (`foretell-vista-main/`).

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### API base URL

- `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

