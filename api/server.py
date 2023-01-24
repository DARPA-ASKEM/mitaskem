from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import code_dataset, code_formula, code_text, avail_check

def build_api(*args) -> FastAPI:

    api = FastAPI(
        title="Annotation API",
        description="MIT annotation API",
        docs_url="/",
    )
    origins = [
        "http://localhost",
        "http://localhost:8080",
    ]
    api.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return api


app = build_api()

app.include_router(code_dataset.router, prefix="/code_dataset")
app.include_router(code_formula.router, prefix="/code_formula")
app.include_router(code_text.router, prefix="/code_text")
app.include_router(avail_check.router, prefix="/avail_check")
