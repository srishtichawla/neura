from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Neura AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "Neura AI running"}

try:
    from api.routes import router
    from db.postgres import init_db
    app.include_router(router, prefix="/api")
    init_db()
    print("✅ All systems started")
except Exception as e:
    import traceback
    print(f"❌ Startup error: {e}")
    traceback.print_exc()
