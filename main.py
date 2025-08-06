from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse  # <== сюда добавлен FileResponse
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections = []

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>OneVoice</title></head>
        <body>
            <h1>OneVoice сервер работает 🎉</h1>
            <p>WebSocket доступен по адресу: <code>/ws</code></p>
        </body>
    </html>
    """

@app.get("/video")
async def get_video_chat():
    return FileResponse("video_chat.html")

@app.get("/camera")
async def get_camera_test():
    return FileResponse("camera_test.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)

    try:
        if len(connections) == 1:
            await websocket.send_json({"type": "wait"})
        elif len(connections) == 2:
            await connections[0].send_json({"type": "init"})
            await connections[1].send_json({"type": "wait"})
        else:
            await websocket.close()
            return

        while True:
            data = await websocket.receive_json()
            for conn in connections:
                if conn != websocket:
                    await conn.send_json(data)

    except WebSocketDisconnect:
        connections.remove(websocket)
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
