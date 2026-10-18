For your Dell laptop with 24 GB RAM on WSL2, I recommend keeping GhostVision’s vision and animation pipeline, but moving the language model entirely to Ollama. That removes the broken local Transformers model-path dependency and gives you more room for a stronger, more creative model.

I’ve implemented the updated script:

ghostvision_ollama.py

Complete Python replacement · webcam, YOLO, Ollama, microphone, TTS and animated ghost

Download the GhostVision script

## Recommended model stack

[Qwen IA - Suite de modelos de lenguaje de Alibaba Cloud](https://images.openai.com/static-rsc-4/wDD9nK6dE97GsQ5vEzRgKYoxUuxEtIY-N12SfyVm4syJFQV4zhNtaHPPwnYKpzJJMrWcA_zCmUVkSYiz21ZlAOspMgo0BNypfB9mjPG5sgkcBkIJ4e74-3-Nw3b9r9X8Z7lnKRFC3orEXKdA_8TjL4dYbsfomT7PiBz26UH2dHc?purpose=inline)

1\. Brain — Qwen3 8B via Ollama

Recommended starting point

Better room for creative punchlines, conversational context and varied humour than a 1.5B model. The script sends recent detection history and recent jokes to help avoid repetitive roasts. Ollama's local chat API supports this message-based workflow.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+1



[Object Detection with YOLO: Hands-on Tutorial](https://images.openai.com/static-rsc-4/zeN45LvmCHaYGiL9fc0e0d4QaVUUKBjJizwLePVmfxIs02Hso-kG5ZQS9WgrlLesfRakyYyEtxIMOvSGDaxFhoO45gxNd0ZaB3Fo_8fe7NMkvxBZ07K5GuSX6vRwzslgCr5AjGAs9muUJjudRTvWjxwdxzu23xIauSRoym_55_M?purpose=inline)

2\. Eyes — YOLO11n

Lightweight object detection for your webcam. GhostVision uses the detected objects as context for its jokes, while retaining the live camera overlay.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ultralytics.com\&sz=32)

Ultralytics Docs



3\. Voice and personality

- Speech recognition: SpeechRecognition with Google Web Speech recognition.
- Speech output: `pyttsx3`, with eSpeak fallback.
- Face: your existing `face_animation.draw_ghost_face(frame, is_speaking)`.

## Install and run it

Run these commands inside your WSL2 terminal, from your GhostVision project directory.

1\. Pull the model and confirm Ollama is running

```
ollama pull qwen3:8b
ollama list
curl http://127.0.0.1:11434/api/tags
```

The 8B model is a reasonable starting point for 24 GB RAM, although actual speed depends on CPU performance and how much memory WSL2 can use.

2\. Install system audio dependencies

```
sudo apt update
sudo apt install -y espeak-ng portaudio19-dev python3-tk
```

3\. Install Python packages

Activate your existing virtual environment first, then run:

```
python -m pip install -U requests opencv-python ultralytics SpeechRecognition PyAudio pyttsx3
```

4\. Put the replacement script in your project

Save the downloaded file as `roast-master.py` inside your `ghostVision` directory, alongside `face_animation.py`.

Your project should contain at least:

```
ghostVision/
├── roast-master.py
└── face_animation.py
```

Then start it:

```
python roast-master.py
```

The script automatically loads `yolo11n.pt` if it isn't already cached. It calls Ollama at `127.0.0.1:11434` and no longer needs the local Hugging Face model directory.

## What the implementation changes

- Context-aware roasts: passes current detections, recent scene events and recent jokes to the LLM.
- Less repeated commentary: scene-change triggers, a cooldown and recent-joke context reduce repetitive lines.
- Responsive webcam loop: object detection runs periodically while the speech/LLM worker operates separately.
- Safer TTS fallback: if `pyttsx3` fails to initialise or speak, the script tries eSpeak.
- Preserved interaction: say “Ghost” or “GhostVision” followed by your request; press `Q` in the camera window to quit.

One important limitation: the speech recognizer still uses Google's online service. The LLM inference is local, but speech-to-text is not fully offline. Also, WSL2 needs working webcam and microphone access for those features to operate.

I would start with `qwen3:8b` and `yolo11n.pt`, then measure the actual response latency. If roasts are too slow, the first adjustment should be a smaller Ollama model—not removing the contextual prompt that gives GhostVision its personality.