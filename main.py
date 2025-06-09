# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Zaten çalışan sisteminizi import edin
from interactive_qa_dual_ai import DualAITefasQA

app = FastAPI(
    title="TEFAS Analiz API",
    description="Akıllı soru-cevap sistemi",
    version="1.0.0"
)

class AnalyzeRequest(BaseModel):
    question: str

# QA sistemini başlat
qa_system = DualAITefasQA()

@app.post("/analyze/auto")
async def analyze_auto(req: AnalyzeRequest):
    """Soruyu analiz et ve cevapla"""
    try:
        result = qa_system.answer_question(req.question)
        return {
            "status": "ok",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "message": "TEFAS API çalışıyor",
        "endpoints": {
            "analyze": "/analyze/auto",
            "docs": "/docs",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    # main.py olduğu için main:app kullan
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)