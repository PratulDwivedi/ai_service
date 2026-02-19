from fastapi import FastAPI
from app.api.routes import auth, chat, docs
from app.core.config import settings
from fastapi.responses import HTMLResponse
from app.services.duckdb_service import close_all_dbs

app = FastAPI( title=settings.app_name,version="1.0.0")

# include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(docs.router)

@app.on_event("shutdown")
async def shutdown_event():
    """Close all DuckDB connections on shutdown."""
    close_all_dbs()

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
