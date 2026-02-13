from fastapi import FastAPI
from app.api.routes import health, auth
from app.core.config import settings
from fastapi.responses import HTMLResponse

app = FastAPI( title=settings.app_name,version="1.0.0")

# include routers
app.include_router(health.router)
app.include_router(auth.router)

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
     <title>{settings.app_name}</title>
        <body style="font-family: Arial; text-align:center; margin-top:50px;">
            <h1>🚀 {settings.app_name}</h1>
            <p>Environment: <strong>{settings.environment}</strong></p>
        </body>
    </html>
    """
