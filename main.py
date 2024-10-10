import uvicorn
import search, auth, user
from utils.return_object import returnObject
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from pydantic import BaseModel

class Video(BaseModel):
  title: str
  id: str
  iframe: str
  thumb_url: str

class Playlist(BaseModel):
    title: str
    id: str
    thumbnailUrl: str
    videos: list[Video]

origins = [
    "https://127.0.0.1:8080",
    "https://localhost:4200",
    "http://localhost:4200"
]

app = FastAPI()

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(user.router)

app.add_middleware(CORSMiddleware,
allow_origins=origins,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],)

#endregion

#region routes

@app.get("/")
async def root():
    token_result = await auth.get_token()
    if token_result.success:
        return returnObject(message="Authenticated", success=True, status_code=200)
    else:
        return returnObject(message="Generating token...", success=False, status_code=500) 
    
@app.post("/cache_playlist")
async def cache_playlist(playlist: Playlist):
    try:
        with open('last_playlist.json', 'w', encoding='utf-8') as f:
            j_str = playlist.model_dump_json()
            f.write(j_str)
    except Exception as ex:
        return returnObject(message="Error caching playlist.", success=False, status_code=500)
    
    return returnObject(message="Successfully cached playlist!", success=True, status_code=200)

@app.get("/get_cached_playlist")
async def get_cached_playlist():
    try:
        with open('last_playlist.json', encoding='utf-8') as f:
            playlist = f.read()
    except Exception as ex:
        return returnObject(message="Error fetching cached playlist." + ex, success=False, status_code=500)
    
    return returnObject(message="Successfully retreived cached playlist!", success=True, data=playlist, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080, ssl_keyfile='key.pem', ssl_certfile='cert.pem')