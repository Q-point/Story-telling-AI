#! /usr/bin/env python

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from assistant import lg_agent
from comfyuiapi import *
import piperengine as engine
import asyncio
import random
import uvicorn
import base64
import json

app = FastAPI()

workflowapi = "workflow_api.json"
engine.load('en_GB-alba-medium.onnx')
selected_device_index = 0  # Set your desired device index here

PUNCTUATION = [".", "?", "!", ":", ";", "*", "-", "**"]

async def play_audio_on_device(text, device_index=0):
    engine.say(text)

async def speak(content, device_index=0):
    await play_audio_on_device(content, device_index)

# Dictionary to store WebSocket connections with endpoint identifiers
websocket_connections = {}
try:
    ws, server_address, client_id = open_websocket_connection()
    workflow = load_workflow(workflowapi)
    prompt = json.loads(workflow)
except (ConnectionError, TimeoutError) as e:
    print(f"Failed to connect to the server: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

text_task = None

# Basic CORS settings
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return open("static/index.html", "r").read()

@app.get("/book.png")
async def get_image():
    return FileResponse("static/book.png", media_type="image/png")

@app.websocket("/ws/{endpoint}")
async def websocket_endpoint(websocket: WebSocket, endpoint: str):
    await websocket.accept()
    websocket_connections[endpoint] = websocket
    try:
        while True:
            await asyncio.sleep(1)  # Keep the connection open to receive messages
    except asyncio.CancelledError:
        pass  # Handle task cancellation gracefully
    except WebSocketDisconnect:
        del websocket_connections[endpoint]  # Remove the connection from the dictionary

# @app.websocket("/ws/{endpoint}")
# async def websocket_endpoint(websocket: WebSocket, endpoint: str):
    # while True:
        # try:
            # await websocket.accept()
            # websocket_connections[endpoint] = websocket
            # try:
                # while True:
                    # await asyncio.sleep(1)  # Keep the connection open to receive messages
            # except asyncio.CancelledError:
                # pass  # Handle task cancellation gracefully
            # except WebSocketDisconnect:
                # print(f"Client {endpoint} disconnected")
                # break
        # except Exception as e:
            # print(f"Error in /ws/{endpoint} WebSocket: {e}")
        # finally:
            # if endpoint in websocket_connections:
                # del websocket_connections[endpoint]
            # await asyncio.sleep(1)  # Delay before attempting to reconnect
            
# Function to send data to the specified WebSocket endpoint
async def send_to_endpoint(endpoint: str, data: str):
    if endpoint in websocket_connections:
        websocket = websocket_connections[endpoint]
        try:
            await websocket.send_text(data)
        except Exception as e:
            print(f"Error sending data to {endpoint}: {e}")


@app.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:  
        try:
            async for message in websocket.iter_text():
                word = ""
                sentence = ""
                try:
                    async for event in lg_agent.astream_events(
                            {"messages": ("user", message)},
                            config={"configurable": {"thread_id": 1}},
                            version="v1"):
                        kind = event["event"]

                        if kind == "on_chat_model_stream":
                            token = event["data"]["chunk"].content
                            if token:
                                if token.startswith(" "):
                                    if word:
                                        await websocket.send_text(word)
                                        sentence += word
                                    word = token
                                else:
                                    word += token

                                if any(token.endswith(punct) for punct in PUNCTUATION):
                                    sentence += word
                                    print(sentence.strip())
                                    
                                    positive_prompt = sentence.strip()                       
                                    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
                                    k_sampler_id = next(key for key, value in id_to_class_type.items() if value == 'KSampler')
                                    k_sampler = prompt[k_sampler_id]

                                    k_sampler['inputs']['seed'] = generate_random_15_digit_number()

                                    positive_input_id = k_sampler['inputs']['positive'][0]
                                    prompt[positive_input_id]['inputs']['text'] = positive_prompt
                                    print("prompting ")
                                    prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
                                    track_progress(prompt, ws, prompt_id)
                                    
                                    print("prompt id" + prompt_id)
                                    print("server_address" + server_address)

                                    images = get_images(prompt_id, server_address, False)  

                                    output_images = get_images(prompt_id, server_address, False)
                                    image_data = get_image_data(output_images)
                                    if image_data:
                                        base64_image = base64.b64encode(image_data).decode('utf-8')
                                        await send_to_endpoint("image", base64_image)
                                    await speak(sentence, selected_device_index)
                                    sentence = ""
                                    word = ""

                    # Send the final partial message if any
                    if word:
                        await websocket.send_text(word)
                        sentence += word
                    if sentence:
                        print(sentence.strip())
                        positive_prompt = sentence.strip()                       
                        id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
                        k_sampler_id = next(key for key, value in id_to_class_type.items() if value == 'KSampler')
                        k_sampler = prompt[k_sampler_id]

                        k_sampler['inputs']['seed'] = generate_random_15_digit_number()

                        positive_input_id = k_sampler['inputs']['positive'][0]
                        prompt[positive_input_id]['inputs']['text'] = positive_prompt
                        print("prompting ")
                        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
                        track_progress(prompt, ws, prompt_id)
                        
                        print("prompt id" + prompt_id)
                        print("server_address" + server_address)

                        images = get_images(prompt_id, server_address, False)  

                        output_images = get_images(prompt_id, server_address, False)
                        image_data = get_image_data(output_images)
                        if image_data:
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            await send_to_endpoint("image", base64_image)
                        await speak(sentence, selected_device_index)

                except Exception as e:
                    try:
                        await websocket.send_text(f"Error: {e}")
                    except RuntimeError as re:
                        print(f"Error sending error message to WebSocket: {re}")
                        break
        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            try:
                await websocket.send_text(f"Error: {e}")
            except RuntimeError as re:
                print(f"Error sending error message to WebSocket: {re}")
        finally:
            # Instead of closing, just log and continue
            print("Restarting WebSocket connection")



# Example of starting the FastAPI app using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

