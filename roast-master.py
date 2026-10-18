#!/usr/bin/env python3
"""
GhostVision: local, context-aware roast assistant.

Stack:
- Ultralytics YOLO11n for webcam object detection
- Ollama (default: qwen3:8b) for creative, context-aware responses
- SpeechRecognition + Google Web Speech API for microphone input
- pyttsx3 / eSpeak NG for local text-to-speech
- face_animation.draw_ghost_face(frame, cx, cy, scale, is_speaking, frame_count)

Run from the GhostVision project directory after installing dependencies and pulling
the Ollama model.
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
import time
from collections import deque

import cv2
import requests
import speech_recognition as sr
from ultralytics import YOLO

import random

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from face_animation import draw_ghost_face


# ----------------------------- Configuration -----------------------------

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolo11n.pt")
CAMERA_INDEX = int(os.getenv("GHOSTVISION_CAMERA", "0"))
FRAME_WIDTH = int(os.getenv("GHOSTVISION_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("GHOSTVISION_HEIGHT", "480"))
YOLO_IMGSZ = int(os.getenv("GHOSTVISION_IMGSZ", "416"))
YOLO_CONFIDENCE = float(os.getenv("GHOSTVISION_CONFIDENCE", "0.35"))
ROAST_COOLDOWN_SECONDS = float(os.getenv("GHOSTVISION_ROAST_COOLDOWN", "12"))
# Ghost face size in PIXELS (glow radius is about scale * 2.8).
FACE_SCALE = int(os.getenv("GHOSTVISION_FACE_SCALE", "28"))
MAX_CONTEXT_EVENTS = 12
MAX_NEW_TOKENS = 110
HTTP_TIMEOUT_SECONDS = 90

SYSTEM_PROMPT = """You are GhostVision, a witty, theatrical, slightly spooky roast-comedian
living inside a webcam. Your job is to make short, creative, context-aware roasts based
on the detected objects and what the user says.

Rules:
- Be playful and clever, not cruel. No slurs, threats, sexual content, or attacks on
  protected traits. Avoid sensitive personal assumptions.
- Roast the situation, objects, posture-free scene, or harmless choices—not a person's
  body, identity, disability, or other sensitive traits.
- Use the visible object labels as clues, not as proof of hidden facts.
- Do not claim to know a person's name, feelings, job, wealth, or intentions.
- Usually produce one punchy sentence, ideally 8–25 words.
- Avoid repeating recent jokes. Vary style: deadpan, absurd, mock-dramatic, nerdy,
  spooky, or sarcastic.
- If the user asks a question, answer it briefly with GhostVision's personality.
- If detections are empty or uncertain, do not invent objects. You may make a joke
  about the mysterious scene instead.
- Output only the line to be spoken; no labels, quotation marks, or stage directions.
"""

# Shared state. Webcam inference stays on the main thread; Ollama and audio use workers.
stop_event = threading.Event()
is_speaking = threading.Event()
state_lock = threading.Lock()
scene_labels: list[str] = []
scene_updated_at = 0.0
recent_events: deque[str] = deque(maxlen=MAX_CONTEXT_EVENTS)
recent_roasts: deque[str] = deque(maxlen=6)
last_auto_roast_at = 0.0
work_queue: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=4)


def set_scene(labels: list[str]) -> None:
    global scene_labels, scene_updated_at
    with state_lock:
        scene_labels = labels
        scene_updated_at = time.time()
        if labels:
            event = "Detected: " + ", ".join(labels)
            if not recent_events or recent_events[-1] != event:
                recent_events.append(event)


def get_context() -> tuple[list[str], list[str]]:
    with state_lock:
        return list(scene_labels), list(recent_events)


def check_ollama() -> None:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=4)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = [m.get("name", "") for m in models]
        if not any(name == OLLAMA_MODEL or name.startswith(OLLAMA_MODEL + ":") for name in names):
            raise RuntimeError(
                f"Ollama is running, but model '{OLLAMA_MODEL}' is not installed.\n"
                f"Available models: {', '.join(names) or '(none)'}\n"
                f"Run: ollama pull {OLLAMA_MODEL}"
            )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_HOST}.\n"
            "Start Ollama in WSL2 (or configure OLLAMA_HOST), then retry."
        ) from exc


def ask_ollama(user_text: str, trigger: str) -> str:
    labels, events = get_context()
    scene = ", ".join(labels) if labels else "No confident objects currently detected"
    history = "\n".join(f"- {event}" for event in events[-8:]) or "- No recent scene events"
    recent_jokes = "\n".join(f"- {joke}" for joke in list(recent_roasts)[-5:]) or "- None yet"

    prompt = f"""Current trigger: {trigger}
Current camera detections: {scene}
Recent scene history:
{history}
Recent jokes to avoid repeating:
{recent_jokes}
User said: {user_text or "(no spoken request; create a scene-based roast)"}

Create one fresh, context-aware GhostVision line. Use the current detections and recent
history when relevant, but don't simply list object labels."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.9,
            "top_p": 0.92,
            "repeat_penalty": 1.15,
            "num_predict": MAX_NEW_TOKENS,
            "num_ctx": 4096,
            "seed": random.randint(0, 2**31 - 1)
        },
    }
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat", json=payload, timeout=HTTP_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    result = response.json().get("message", {}).get("content", "").strip()
    if not result:
        raise RuntimeError("Ollama returned an empty response.")
    # Keep the spoken line short even if the model ignores the instruction.
    return " ".join(result.split())[:500]


def speak_with_windows(text: str) -> bool:
    """Use Windows' built-in speech engine from WSL (no Linux audio needed)."""
    ps = shutil.which("powershell.exe")
    if not ps:
        return False
    # Escape every kind of single quote for PowerShell.
    for ch in "'\u2018\u2019\u201a\u201b":
        text = text.replace(ch, "''")
    cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Speak('{text}')"
    )
    try:
        subprocess.run(
            [ps, "-NoProfile", "-Command", cmd],
            check=False, timeout=45,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def speech_worker() -> None:
    """Serially generate and speak lines so audio never overlaps itself."""
    engine = None
    if pyttsx3 is not None:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.setProperty("volume", 0.95)
        except Exception as exc:
            print(f"[TTS] pyttsx3 unavailable; will try eSpeak NG: {exc}")
            engine = None

    while not stop_event.is_set():
        try:
            trigger, user_text = work_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        try:
            is_speaking.set()
            print(f"\n[GhostVision] Thinking ({OLLAMA_MODEL})...")
            line = ask_ollama(user_text, trigger)
            print(f"[GhostVision] {line}")
            recent_roasts.append(line)

            spoken = False
            if engine is not None:
                try:
                    engine.say(line)
                    engine.runAndWait()
                    spoken = True
                except Exception as exc:
                    print(f"[TTS] pyttsx3 failed; trying eSpeak NG: {exc}")
                    try:
                        engine.stop()
                    except Exception:
                        pass
                    engine = None

            if not spoken:
                spoken = speak_with_windows(line)

            if not spoken:
                # No audio backend (common in WSL). Keep the mouth animating briefly
                # so the on-screen ghost still "talks".
                time.sleep(min(6.0, 0.35 * len(line.split())))
        except requests.RequestException as exc:
            print(f"[Ollama] Request failed: {exc}")
        except Exception as exc:
            print(f"[GhostVision] Error: {exc}")
        finally:
            is_speaking.clear()
            work_queue.task_done()


def enqueue_line(trigger: str, user_text: str = "") -> bool:
    try:
        work_queue.put_nowait((trigger, user_text))
        return True
    except queue.Full:
        print("[GhostVision] Busy right now; skipping this trigger.")
        return False


def microphone_worker() -> None:
    """Google speech recognition is online; Ollama generation remains local."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.7

    try:
        microphone = sr.Microphone()
    except Exception as exc:
        print(f"[Mic] Could not open microphone: {exc}")
        print("[Mic] Camera mode will continue; speech input is disabled.")
        return

    with microphone as source:
        print("[Mic] Calibrating ambient noise...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception as exc:
            print(f"[Mic] Calibration warning: {exc}")

    print("[Mic] Listening. Say 'Ghost' or 'GhostVision' to address me.")
    while not stop_event.is_set():
        try:
            with microphone as source:
                audio = recognizer.listen(source, timeout=1.0, phrase_time_limit=6)
            spoken = recognizer.recognize_google(audio).strip()
            if not spoken:
                continue
            print(f"[You] {spoken}")
            lowered = spoken.lower()
            if "ghostvision" in lowered or "ghost" in lowered:
                cleaned = spoken
                for word in ("GhostVision", "ghostvision", "Ghost", "ghost"):
                    cleaned = cleaned.replace(word, "").strip(" ,.!?")
                enqueue_line("spoken request", cleaned or "Roast the current scene.")
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as exc:
            print(f"[Mic] Speech recognition service unavailable: {exc}")
            time.sleep(2)
        except Exception as exc:
            print(f"[Mic] Listener warning: {exc}")
            time.sleep(1)


def open_camera() -> cv2.VideoCapture:
    """Open the webcam with settings that work reliably over usbipd/WSL2."""
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    # FOURCC must be set before width/height so the driver negotiates MJPG.
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not camera.isOpened():
        raise RuntimeError(
            f"Could not open camera index {CAMERA_INDEX}. "
            "Check WSL2 webcam access (usbipd attach) or try GHOSTVISION_CAMERA=1."
        )
    return camera


def main() -> None:
    global last_auto_roast_at

    print("Checking local Ollama...")
    check_ollama()
    print(f"[Ollama] Connected; model: {OLLAMA_MODEL}")

    print(f"Loading detector: {YOLO_MODEL}")
    detector = YOLO(YOLO_MODEL)

    camera = open_camera()

    threading.Thread(target=speech_worker, name="ghost-speech", daemon=True).start()
    threading.Thread(target=microphone_worker, name="ghost-mic", daemon=True).start()

    print("\nGhostVision is live. Press Q in the camera window to quit.")
    print("Auto-roasts trigger when the detected scene changes; say 'Ghost ...' for a request.")

    previous_signature: tuple[str, ...] = ()
    last_detection_time = 0.0
    cached_annotated = None
    frame_count = 0

    try:
        while not stop_event.is_set():
            ok, frame = camera.read()
            if not ok:
                print("[Camera] Frame read failed; retrying...")
                time.sleep(0.1)
                continue

            now = time.time()
            # Run detector a few times per second; reuse last overlay between inference passes.
            if now - last_detection_time >= 0.25 or cached_annotated is None:
                result = detector.predict(
                    source=frame,
                    imgsz=YOLO_IMGSZ,
                    conf=YOLO_CONFIDENCE,
                    verbose=False,
                    device="cpu",
                )[0]
                labels = []
                if result.boxes is not None:
                    for class_id in result.boxes.cls.tolist():
                        name = detector.names.get(int(class_id), str(class_id))
                        if name not in labels:
                            labels.append(name)
                labels = labels[:8]
                set_scene(labels)
                signature = tuple(sorted(labels))

                # Trigger only when the set of visible object classes changes.
                if signature != previous_signature and signature and (
                    now - last_auto_roast_at >= ROAST_COOLDOWN_SECONDS
                ):
                    if enqueue_line("scene changed"):
                        last_auto_roast_at = now
                    previous_signature = signature
                elif signature != previous_signature:
                    previous_signature = signature

                cached_annotated = result.plot()
                last_detection_time = now

            display = cached_annotated.copy() if cached_annotated is not None else frame.copy()

            # Ghost avatar in the top-right corner. FACE_SCALE is in pixels;
            # the glow ring radius is about FACE_SCALE * 2.8.
            frame_count += 1
            h, w = display.shape[:2]
            margin = int(FACE_SCALE * 2.8) + 10
            draw_ghost_face(
                display,
                cx=w - margin,
                cy=margin,
                scale=FACE_SCALE,
                is_speaking=is_speaking.is_set(),
                frame_count=frame_count,
            )

            cv2.putText(
                display,
                f"LLM: {OLLAMA_MODEL} | Say 'Ghost ...' to ask | Q: quit",
                (10, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (80, 255, 120),
                1,
                cv2.LINE_AA,
            )
            cv2.imshow("GhostVision", display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        stop_event.set()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping GhostVision...")
        stop_event.set()
    except Exception as error:
        print(f"\n[FATAL] {error}")
        print(
            "\nQuick checks:\n"
            "  ollama list\n"
            "  curl http://127.0.0.1:11434/api/tags\n"
            "  python -c \"from face_animation import draw_ghost_face; print('animation import OK')\""
        )
        raise