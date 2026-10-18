# 👻 ghostVision: The Roast Master Agent

### Surrounded by non-living things. Haunted by their opinions.

**ghostVision** is a local-first, voice-controlled AI agent that gives
everyday objects a mischievous personality. It uses computer vision to
spot objects through your webcam, then asks a local language model to
turn the scene into a witty, context-aware roast.

It has **eyes** (YOLO object detection), **ears** (speech recognition),
and a **voice** (text-to-speech). The result: an animated ghost that
watches the room and has *opinions*.

> Your objects have been silent for too long. ghostVision gives them a
> voice---and absolutely no chill.

------------------------------------------------------------------------

## 💡 Motivation: The Inanimate Rebellion

### What if non-living things could talk?

Most AI assistants are designed to be helpful, polite, and predictable.
ghostVision takes a different approach: what if your desk, chair, coffee
mug, old laptop, or questionable phone could comment on the scene?

Instead of turning object detection into another dry list of labels,
ghostVision uses those detections as context for playful,
situation-aware comedy.

### The core concept: Spatial satire

ghostVision combines **computer vision**, **local language-model
inference**, **speech interaction**, and **animated visuals**. It
transforms a webcam feed into a small interactive comedy show---without
sending prompts to a hosted LLM API.

------------------------------------------------------------------------

## 🚀 Features

-   **👁️ Real-time object detection:** Uses Ultralytics YOLO11n to
    detect objects in the webcam feed.
-   **🧠 Local LLM brain:** Uses Qwen3 8B through Ollama for creative,
    context-aware responses.
-   **🎙️ Voice interaction:** Say **"Ghost"** or **"GhostVision"**
    followed by a request to address the agent.
-   **🔥 Automatic scene roasts:** A change in detected object classes
    can trigger a roast, subject to a cooldown.
-   **🧩 Context-aware humour:** Sends current detections, recent scene
    events, and recent jokes to the model to encourage variety.
-   **🔊 Speech output:** Uses `pyttsx3` when available, with an
    eSpeak/eSpeak NG fallback.
-   **👻 Animated ghost face:** Reuses
    `face_animation.draw_ghost_face(frame, is_speaking)` to animate the
    face on the camera display.
-   **🧵 Background workers:** Keeps language generation and speech
    handling separate from the main camera loop.
-   **🏠 Local LLM inference:** Ollama runs the language model on your
    machine; no Hugging Face model folder is required by the app.

> **Privacy note:** LLM prompts are sent to your local Ollama instance.
> The current speech-recognition implementation uses Google Web Speech
> via `SpeechRecognition`, so microphone audio is sent to Google's
> recognition service. Speech recognition is therefore **not fully
> offline**.

------------------------------------------------------------------------

## 🧠 How It Works

``` text
Webcam
  │
  ▼
OpenCV frame capture
  │
  ▼
YOLO11n object detection
  │
  ├──► Annotated camera feed
  │
  ▼
Current detections + recent scene history
  │
  ▼
Ollama: Qwen3 8B
  │
  ▼
Short, context-aware roast
  │
  ▼
pyttsx3 / eSpeak NG ──► Speakers
  │
  ▼
Animated ghost face reacts while speaking

Microphone ──► SpeechRecognition / Google Web Speech
                       │
                       └──► Voice request to the local Ollama model
```

The object labels are clues for the joke, not proof of hidden facts.
ghostVision is intended for playful commentary---not surveillance or
high-stakes decisions.

------------------------------------------------------------------------

## 🛠️ Tech Stack

  Component                    Technology
  ---------------------------- -------------------------------------------
  Object detection             Ultralytics YOLO11n
  Local language model         Qwen3 8B
  Local model runtime          Ollama
  Camera and rendering         OpenCV
  Speech-to-text               SpeechRecognition + PyAudio
  Speech recognition service   Google Web Speech API
  Text-to-speech               `pyttsx3`, with eSpeak/eSpeak NG fallback
  Concurrency                  Python `threading` and `queue`
  Animated face                `face_animation.py`

------------------------------------------------------------------------

## 📦 Installation & Setup

### 1. Prerequisites

-   Python 3.10 or newer
-   A working webcam and microphone accessible from your environment
-   [Ollama](https://ollama.com/) installed and running
-   A Linux audio backend for TTS if running in WSL2
-   The `face_animation.py` module in the project directory

### 2. Pull the language model

Start Ollama, then run:

``` bash
ollama pull qwen3:8b
ollama list
```

Check that the Ollama API is reachable:

``` bash
curl http://127.0.0.1:11434/api/tags
```

The default model is `qwen3:8b`. You can change it with the
`OLLAMA_MODEL` environment variable.

### 3. Install system dependencies on Ubuntu/WSL2

``` bash
sudo apt update
sudo apt install -y espeak-ng portaudio19-dev python3-tk
```

**WSL2 note:** Webcam, microphone, and audio passthrough depend on your
Windows/WSL setup. If OpenCV cannot open the camera, verify that the
device is exposed to Linux or try a different camera index.

### 4. Create and activate a virtual environment

From the project directory:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 5. Install Python dependencies

``` bash
python -m pip install requests opencv-python ultralytics SpeechRecognition PyAudio pyttsx3
```

The first YOLO run may download `yolo11n.pt` automatically if the
weights are not already cached.

### 6. Run ghostVision

Save the main script as `roast-master.py`, keep `face_animation.py`
beside it, and run:

``` bash
python roast-master.py
```

Press **Q** in the camera window to quit.

------------------------------------------------------------------------

## 🎮 How to Use

1.  **Launch the agent:** Run `python roast-master.py`.
2.  **Wait for startup:** ghostVision checks Ollama, loads YOLO, and
    opens the camera.
3.  **Show it something:** Point the camera at an object. Detected
    classes appear in the annotated feed.
4.  **Summon the ghost:** Say **"Ghost, what do you think of this
    phone?"** or **"GhostVision, roast this setup."**
5.  **Watch and listen:** The model generates a line, the TTS system
    speaks it, and the animated ghost face reacts while speaking.
6.  **Try scene-triggered roasts:** A change in detected object classes
    can automatically trigger a roast after the cooldown.

The current implementation does **not** require the exact phrase
"Activate Roast Mode." It also does not promise to draw a separate face
on every detected object or show scrolling subtitles; the ghost
animation is drawn on the camera display.

------------------------------------------------------------------------

## 🔥 The Burn Log

Example lines---the model generates its own response at runtime, so
exact wording will vary.

  -----------------------------------------------------------------------
  Object or scene                     Example roast
  ----------------------------------- -----------------------------------
  POCO phone                          "That phone has the confidence of a
                                      flagship and the survival instincts
                                      of a microwave."

  Old laptop                          "That fan isn't cooling the CPU;
                                      it's filing a noise complaint."

  Empty coffee cup                    "Empty already? Your productivity
                                      arc has a familiar plot."

  Desk full of gadgets                "A whole ecosystem of devices, and
                                      somehow the biggest bottleneck is
                                      still the operator."

  Mysterious scene                    "Nothing detected. Either the room
                                      is empty or the ghosts have learned
                                      stealth."
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## ⚙️ Configuration

You can configure the app with environment variables before running it.

  ---------------------------------------------------------------------------------
  Variable                       Default                    Purpose
  ------------------------------ -------------------------- -----------------------
  `OLLAMA_HOST`                  `http://127.0.0.1:11434`   Ollama API base URL

  `OLLAMA_MODEL`                 `qwen3:8b`                 Ollama model tag

  `YOLO_MODEL`                   `yolo11n.pt`               YOLO weights/model

  `GHOSTVISION_CAMERA`           `0`                        Camera index

  `GHOSTVISION_WIDTH`            `640`                      Camera frame width

  `GHOSTVISION_HEIGHT`           `480`                      Camera frame height

  `GHOSTVISION_IMGSZ`            `416`                      YOLO inference image
                                                            size

  `GHOSTVISION_CONFIDENCE`       `0.35`                     Detection confidence
                                                            threshold

  `GHOSTVISION_ROAST_COOLDOWN`   `12`                       Minimum seconds between
                                                            automatic scene roasts
  ---------------------------------------------------------------------------------

Example:

``` bash
OLLAMA_MODEL=qwen3:8b GHOSTVISION_ROAST_COOLDOWN=20 python roast-master.py
```

For a different model, pull it with Ollama first and then set
`OLLAMA_MODEL` to its installed tag.

------------------------------------------------------------------------

## 🧠 The Molt Philosophy

> "Why settle for a helpful assistant when your hardware could have a
> personality? The objects are innocent. Their opinions about your setup
> are not."

ghostVision is an experiment in **local AI, computer vision, and playful
human-computer interaction**. Its goal is to make AI feel less like a
command line and more like a mischievous presence in the room.

------------------------------------------------------------------------

## 🧯 Troubleshooting

### Ollama connection refused

Make sure Ollama is running and check:

``` bash
ollama list
curl http://127.0.0.1:11434/api/tags
```

If Ollama runs on Windows rather than inside WSL2, `127.0.0.1` may not
point to the Windows host in your setup. Set `OLLAMA_HOST` to the
reachable host address.

### Model not found

``` bash
ollama pull qwen3:8b
ollama list
```

If you use another model, set `OLLAMA_MODEL` to the exact installed
model tag.

### Camera cannot open

Check camera access from WSL2 and try another index:

``` bash
GHOSTVISION_CAMERA=1 python roast-master.py
```

### Microphone does not work

Check that PyAudio can access a microphone from your environment. The
current Google speech-recognition path also requires network access.

### `pyttsx3` voice error

Install eSpeak NG:

``` bash
sudo apt install -y espeak-ng
espeak-ng "GhostVision is awake."
```

The script attempts to fall back to eSpeak if `pyttsx3` fails.

### Slow responses

Language generation and speech are CPU/RAM dependent. Close other heavy
applications, lower `GHOSTVISION_IMGSZ`, or use a smaller Ollama model
if response latency is too high.

------------------------------------------------------------------------

## 🗺️ Roadmap Ideas

-   Optional fully offline speech recognition (for example, a local
    Whisper-based path)
-   Configurable roast intensity and comedy styles
-   Persistent memory for recurring objects and past jokes
-   More robust scene-change tracking than object-class changes alone
-   Optional object-specific overlays and on-screen captions

------------------------------------------------------------------------

## 📜 Disclaimer

ghostVision is an experimental comedy project. Object detection can be
wrong, speech recognition can mishear you, and generated roasts can be
awkward or inaccurate. Keep the humour playful and do not use the system
to identify people or make consequential judgments.
