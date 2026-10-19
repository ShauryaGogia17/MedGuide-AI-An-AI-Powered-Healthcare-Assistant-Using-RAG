"""Run from ai-service: python -m uvicorn main:app --reload --port 8000."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_ORIGIN
from api.routes.document_routes import router as document_router
from api.routes.rag_routes import router as rag_router
from api.routes.ml_routes import router as ml_router
from api.routes.language_routes import router as language_router
from api.routes.blood_routes import router as blood_router

app=FastAPI(title='MedGuide AI',version='0.2.0')
app.add_middleware(CORSMiddleware,allow_origins=[FRONTEND_ORIGIN],allow_methods=['GET','POST'],allow_headers=['Content-Type'])
app.include_router(document_router)
app.include_router(rag_router)
app.include_router(ml_router)
app.include_router(language_router)
app.include_router(blood_router)

@app.get('/')
def home():return {'message':'MedGuide AI is running'}

@app.get('/health')
def health():return {'status':'ok','service':'ai-service'}
