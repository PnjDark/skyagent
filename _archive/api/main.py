import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.webhooks import router as webhooks_router
from api.scoring import router as scoring_router
from api.content import router as content_router
from api.buffer import router as buffer_router
from api.portfolio import router as portfolio_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(webhooks_router, prefix='/webhooks')
app.include_router(scoring_router, prefix='/scoring')
app.include_router(content_router, prefix='/content')
app.include_router(buffer_router, prefix='/buffer')
app.include_router(portfolio_router, prefix='/portfolio')

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/')
def root():
    return {'name': 'Focus Engine API', 'status': 'ok'}

if __name__ == '__main__':
    uvicorn.run('api.main:app', host='0.0.0.0', port=8000)
