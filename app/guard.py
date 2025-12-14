"""
This file downloads images from the incoming streams and processes them using
local LLMs. It acts as the "guard" to detect anomalies.
"""

import os
from ollama import Client
import requests
from multiprocessing import Process
from time import sleep
import base64
import datetime

from config import STREAMS, OLLAMA_HOST, OLLAMA_MODEL, NTFY_CHANNEL, Config

BOUNDARY = "BLIPBOUNDARY"


IDENTIFY_PROMPT = """You are a security guard.

You are given two frames: The first one is guaranteed to be a safe, normal \
state of the room observed. The next frame is a live feed from the camera.

Your task is to identify if there is anything suspicious in the frame you are \
given. Ignore pets like cats and dogs.

If a bag, jacket or any other object has moved, that's fine. But if a door is \
suddenly open, or a person is in the frame, or something else is there that \
is definitely not normal, then you should ring the alarm.

If you see something that's definitely suspicious, respond with "[RING ALARM]".
Ringing the alarm is an EXTREMELY expensive and SERIOUS action, so only do it \
if you are 100% CERTAIN that something is happening. NEVER ELSE!

If everything is fine or just slightly off, respond with "[ALL CLEAR]".

Before answering, engage in an elaborate thinking process where you check all \
these points one by one. Talk to youself, do not rush."""

EXPLAIN_PROMPT = """You are a security guard.

You are monitoring a live video stream from a camera. Previously, you have \
identified something suspicious in the frame you are given. Now, your task is \
to explain briefly what's suspicious in the frame you are given. This message \
will be sent to the owners.

Accurately describe the scene you see in the frame. DO NOT ANSWER ANYTHING \
ELSE, no preamble, no greeting, no question at the end."""


def save_suspicious_frame(frame):
    """
    Saves the suspicious frame to a file.
    This is useful for debugging and testing purposes.
    """

    if not os.path.isdir("suspicious-frames"):
        os.mkdir("suspicious-frames")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    with open(os.path.join("suspicious-frames", f"{timestamp}.jpg"), "wb") as f:
        f.write(base64.b64decode(frame))


def stream_to_url(stream):
    """
    Adds /cam.mjpg to the end of the stream URL.
    """

    return f"{stream}/cam.mjpg"


def download_frame(url):
    """
    Frames are MJPG-Encoded and use the boundary string to separate them.
    This function downloads a frame from the given URL and returns it as base64
    encoded string to prompt into Ollama.

    Important: This is a never-ending MJPG stream (octets) and we need to
    handle it appropriately to extract a single frame.
    """

    print("making request to", url)
    response = requests.get(url, stream=True)

    def to_base64(data):
        """
        Converts binary data to base64 encoded string.
        """

        return base64.b64encode(data).decode("utf-8")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    boundary_bytes = ("--" + BOUNDARY).encode("utf-8")

    buffer = b""
    frame_data = None

    for chunk in response.iter_content(chunk_size=1024):
        if not chunk:
            continue

        buffer += chunk

        while True:
            boundary_start = buffer.find(boundary_bytes)

            if boundary_start == -1:
                break

            if boundary_start == 0:
                boundary_end = buffer.find(b"\n", len(boundary_bytes))

                if boundary_end == -1:
                    break

                buffer = buffer[boundary_end + 1 :]
                continue

            frame_data = buffer[:boundary_start]

            buffer = buffer[boundary_start:]
            break

        if frame_data is not None:
            header_end = frame_data.find(b"\r\n\r\n")

            if header_end == -1:
                frame_data = None
                continue

            image_data = frame_data[header_end + 4 :]

            return to_base64(image_data)

    raise RuntimeError("Could not find a frame in the stream")


def prompt_model(frame, okay_frame, client):
    """
    Prompts the Ollama model with the given frame.
    """

    while True:
        answer = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": IDENTIFY_PROMPT,
                },
                {
                    "role": "user",
                    "content": "This is how the place normally looks. If it \
still looks like this, everything is fine.",
                    "images": [okay_frame],
                },
                {
                    "role": "user",
                    "content": "Is there anything suspicious in this frame?",
                    "images": [frame],
                },
            ],
            stream=False,
            options={
                "temperature": 0.1,
                "num_predict": 512,
            }
        )["message"]["content"].strip()

        print("Model response:", answer)

        if "[RING ALARM]" in answer:
            return True
        elif "[ALL CLEAR]" in answer:
            return False
        elif "[FLAG FRAME]" in answer:
            print("Frame flagged, not ringing the alarm.")
            return False


def explain_danger(frame, client):
    answer = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": EXPLAIN_PROMPT,
            },
            {
                "role": "user",
                "content": "Explain.",
                "images": [frame],
            },
        ],
        stream=False,
    )["message"]["content"].strip()

    return answer


def ring_alarm(explanation):
    requests.post(
        f"https://ntfy.sh/{NTFY_CHANNEL}",
        data=f"""**Something suspicious has been detected.**

Blip guard explanation:

{explanation}""",
        headers={"Priority": "5", "Tags": "rotating_light", "Markdown": "yes"},
    )


def mainloop():
    """
    Main loop of the guard service.
    Monitors the streams and checks for suspicious activity.
    """

    print("Starting guard service...")

    client = Client(OLLAMA_HOST)

    okay_frames = {k: "" for k in STREAMS}

    while True:
        for stream in STREAMS:
            if okay_frames[stream] == "":
                print("Downloading initial frame for", stream)
                url = stream_to_url(stream)
                okay_frames[stream] = download_frame(url)

            print("Downloading frame from", stream)

            url = stream_to_url(stream)
            frame = download_frame(url)

            if frame is None:
                print(f"Failed to download frame from {url}")
                continue

            print("Frame downloaded, prompting model...")
            if prompt_model(frame, okay_frames[stream], client):
                print("Suspicious activity detected, explaining...")

                try:
                    requests.post(
                        "http://localhost:5000/api/report",
                        json={"message": "alarm", "secret_key": Config.SECRET_KEY},
                        timeout=2
                    )
                except requests.RequestException as e:
                    print("Failed to notify the web app:", e)

                explanation = explain_danger(frame, client)
                ring_alarm(explanation)

                try:
                    requests.post(
                        "http://localhost:5000/api/report",
                        json={"message": explanation, "secret_key": Config.SECRET_KEY},
                        timeout=2
                    )
                except requests.RequestException as e:
                    print("Failed to notify the web app:", e)

                save_suspicious_frame(frame)

                sleep(360)
            else:
                try:
                    requests.post(
                        "http://localhost:5000/api/report",
                        json={"message": "ok", "secret_key": Config.SECRET_KEY},
                        timeout=2
                    )
                except requests.RequestException as e:
                    print("Failed to notify the web app:", e)


def start_background_job():
    """
    Starts this guard service as a separate process.
    """

    process = Process(target=mainloop)
    process.start()

    return process
