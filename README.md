# AI Service

This project is a production‑grade FastAPI template with:

* Clean architecture structure
* Supabase integration
* JWT authentication
* AI agent skeleton

## Prerequisites

* Python 3.9+ installed
* `python3`, `pip3` available in PATH
* (Optional) virtual environment tool such as `venv` or `virtualenv`

## Setup on a new machine

1. **Clone the repository**
   ```bash
   git clone <repo-url> ai-service
   cd ai-service
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   # .\venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip3 install --upgrade pip
   pip3 install -r requirements.txt
   ```

4. **Copy and edit environment file**
   ```bash
   cp .env.example .env      # if an example exists; otherwise edit .env directly
   ```
   Open `.env` and provide values for the following required settings:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   JWT_SECRET=supersecret
   ```
   > The application will fail to start if required variables (like `SUPABASE_URL`)
   > are missing, so make sure this file is populated before running.

5. **Run the development server**
   ```bash
   -- default dev
   uvicorn app.main:app --reload
   -- with env
   ENVIRONMENT=dev uvicorn app.main:app --reload
   ENVIRONMENT=staging uvicorn app.main:app
   ENVIRONMENT=prod uvicorn app.main:app
   ```

6. **API Documents**
   * Swagger UI - http://127.0.0.1:8000/docs
   * Redoc - http://127.0.0.1:8000/redoc


7. **API endpoints**
   * `GET /health` – health check
   * `POST /auth/signup` – register user
   * `POST /auth/login` – authenticate

## Notes

* Always use `python3`/`pip3` as shown; IDEs that rely on `pip` or `python` may default to incorrect versions.
* `requirements.txt` currently specifies:
  ```text
  fastapi
  uvicorn[standard]
  python-jose[cryptography]
  passlib[bcrypt]
  supabase
  pydantic[email]
  email-validator
  ```
* After modifying `requirements.txt`, re-run `pip3 install -r requirements.txt`.
* To add or update dependencies, use `pip3 install <pkg>` then `pip3 freeze > requirements.txt`.

## Running tests

_TBD_

## Deployment

_TBD on future enhancements_
