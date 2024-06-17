# Introduction

This article will outline how to implement a story telling AI application structured as a service oriented architecture. The application makes use of a local LLM server via Ollama, Langraph to implement a stateful graph with memory and ComfyUI to provide story images. Due to the distributed service oriented nature of the application,  the main application communicates via POST requests with the LLM server and via websockets with the diffusion image server. The frontend is built using JQuery and Bootstrap with some custom styling. The backend is based on FastAPI. The AI assistant is implemented using Langgraph. The chatbot makes use of an sqlite db to add persistent memory to any session.
The chat queries are sent to the backend which are then forwarded to the Langgraph agent. 
The chatbot uses the ChatOllama() from the Langchain library in streaming mode. The tokens are converted into full blown sentences and send to a stable diffusion server (Comfyui) via a custom Websocket API.

The program reads a JSON file which specifies the ComfyUI checkpoint model. In this case we are using the darksushi model trained on anime. The dimensions of the images are 256x256 pixel. Note that increasing the image dimensions can cause the app to run out of video memory. The incoming responses are base64 encoded images which are received on the backend and sent to the frontend.
Since the app makes use of the checkpointing features of Langraph is has memory of the chat interaction.

### Configure ComfyUI

1. On Windows , download ComfyUI from [https://github.com/comfyanonymous/ComfyUI/releases/download/latest/ComfyUI_windows_portable_nvidia_cu118_or_cpu.7z](https://github.com/comfyanonymous/ComfyUI/releases/download/latest/ComfyUI_windows_portable_nvidia_cu118_or_cpu.7z) 

[https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)

2. Download dark sushi model

```
wget https://civitai.com/api/download/models/56071
```
Download model and put under ComfyUI\models\checkpoints.
Make sure the name on the JSON file corresponds to the model name: darkSushiMixMix_colorful.safetensors

3. If running on Jetson devices either upgrade to Jetpack 6 to get access to newer python version or create a custom container

Note: Python 3.11 is used on Ubuntu 22.04 to run both PiperTTS and main app.
On Jetson Jetpack 5 one can use Conda for Python 3.11

For Jetpack 5 create a custom container:

```python
PYTHON_VERSION=3.11 jetson-containers build --name=aiapps pytorch:2.2 torchvision:0.17.2 torchaudio:2.2.2 python:3.11 langchain
```
Map , the Comfui folder to the Docker home directory.

```shell
jetson-containers run -p 80:8188 -v /agxorin_ssd/ComfyUI:/home $(autotag aiapps)
```

We have to install additional packages before we start the ComfyUI server on Jetson.

```python
cd home
pip3 install -r requirements.txt
pip3 install --upgrade requests
python3 main.py  --disable-smart-memory --listen 0.0.0.0
```

At this point ComfyUI is installed. Open a web-browser on http://127.0.0.1:8188 and test the basic model. Make sure to change the checkpoint to the model downloaded under /models/checkpoints 

### Configure Ollama
Ollama is available for Windows, Linux and Jetson via Jetson Containers.

On Windows, I used WSL:
1. Install Ollama on WSL from website
2. Run ollama
   
```
ollama run mistral
```

On Jetson:

```
 jetson-containers run --name ollama $(autotag ollama)
 ollama run mistral
```

At this point:

if running on Windows:

ComfyUI and Ollama should be started before the app
If running on Linux :

Same , also make sure to create a python 3.11 environment.



### Configure main application

On Ubuntu 22.04 :
1. Create a python conda environment with any version equal or greater than python 3.11.

```
conda info --envs
conda env remove --name aistory

conda create -n aistory python=3.11
conda activate aistory
pip3 install -r requirements.txt
pip3 install --upgrade requests
pip3 install numexpr
pip install piper-tts

python app.py
conda deactivate
```

2. Install the requirements
3. Upgrade requests separately
4. Install piper-tts for text to speech.
5. Start application, navigate to http://127.0.0.1:8000 and ask the chatbot to provide a story.


On Windows:

1. Text to speech is not yet supported.
2. Same conda envrionment with Python 3.11 works.
3. 

# Notes:

1. The diffusion models are not censored so generated content may be age in-appropriate.
2. The mistral model is used via ChatOllama. The model may be replaced easily. Since they are not censored generated content may also be age-inappropriate.
3. Voice narration is only supported on Linux using Piper-TTS
