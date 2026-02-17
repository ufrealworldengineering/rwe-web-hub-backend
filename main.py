from fastapi import FastAPI
from api.routes.applications.routes import router as applicationRouter
from api.routes.members.routes import router as memberRouter
from api.routes.teams.routes import router as teamRouter
from api.routes.programs.routes import router as programRouter
from api.routes.users.routes import router as userRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

LOCALHOST_PORT = os.getenv("LOCALHOST_PORT")


app = FastAPI(title="RWE Club Portal API")

# Setup CORS so your Frontend (on GitHub Pages) can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ufrealworldengineering.org", f"http://localhost:{LOCALHOST_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applicationRouter, prefix="/api")
app.include_router(userRouter, prefix="/api")
app.include_router(memberRouter, prefix="/api")
app.include_router(teamRouter, prefix="/api")
app.include_router(programRouter, prefix="/api")

@app.get("/")
def root():
    return {"status": "Real World Engineering API is online"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=LOCALHOST_PORT, reload=True)