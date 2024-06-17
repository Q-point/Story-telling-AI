# Introduction

This article will outline how to implement a story telling AI application structured as a service oriented architecture. The application makes use of a local LLM server via Ollama, Langraph to implement a stateful graph with memory and ComfyUI to provide story images. Due to the distributed service oriented nature of the application,  the main application communicates via POST requests with the LLM server and via websockets with the diffusion image server. 

### Configure ComfyUI

1. On Windows , download ComfyUI from [https://github.com/comfyanonymous/ComfyUI/releases/download/latest/ComfyUI_windows_portable_nvidia_cu118_or_cpu.7z](https://github.com/comfyanonymous/ComfyUI/releases/download/latest/ComfyUI_windows_portable_nvidia_cu118_or_cpu.7z) 

[https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)

2. Download dark sushi model
wget https://civitai.com/api/download/models/56071

3. If running on Jetson devices either upgrade to Jetpack 6 to get access to newer python version or create a custom container

For Jetpack 5 create a custom container:


```python
PYTHON_VERSION=3.11 PYTORCH_VERSION=2.3 jetson-containers build --name=aiapps pytorch:2.2 torchvision:0.17.2 torchaudio:2.2.2 python:3.11 langchain
```


Now map , the Comfui folder to the Docker home directory.

```shell
jetson-containers run -p 80:8188 -v /agxorin_ssd/ComfyUI:/home $(autotag aiapps)
```

We have to install additional packages before we start the ComfyUI server.

```python
cd home
pip3 install -r requirements.txt
pip3 install --upgrade requests
python3 main.py  --disable-smart-memory --listen 0.0.0.0
```

At this point ComfyUI is installed. Open a web-browser on http://127.0.0.1:8188 and test the diffusion model.

### Configure Ollama
Ollama is available for Windows, Linux and Jetson via Jetson Containers.

On Windows, I used WSL:
1. Install Ollama on WSL
2. ollama run mistral

On Jetson:

```
 jetson-containers run --name ollama $(autotag ollama)
 ollama run mistral
```

### Configure main application

On Linux :
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
5. Start application
6. Navigate to http://127.0.0.1:8000 and ask the chatbot to provide a kids story.

# Notes:

1. The diffusion models are not censored so generated content may be age in-appropriate.
2. The mistral model is used via ChatOllama. The model may be replaced easily. Since they are not censored generated content may also be age-inappropriate.
3. Voice narration is only supported on Linux using Piper-TTS
