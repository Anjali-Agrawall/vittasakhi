import os
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import run_pipeline_and_collect

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "VittaSakhi API is running"}


@app.post("/process")
async def process(persona: str = Form(...), image: UploadFile = None):
    os.makedirs("uploads", exist_ok=True)
    image_path = f"uploads/{image.filename}"
    with open(image_path, "wb") as f:
        f.write(await image.read())

    result = await run_pipeline_and_collect(persona, image_path)
    return result