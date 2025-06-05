"""
This file downloads
"""

from ollama import Client
import requests
from multiprocessing import Process
from time import sleep
import base64

from config import STREAMS, OLLAMA_HOST, OLLAMA_MODEL, NTFY_CHANNEL

BOUNDARY = "BLIPBOUNDARY"


IDENTIFY_PROMPT = """You are a security guard.

You are monitoring a live video stream from a camera. Your task is to \
identify if there is anything suspicious in the frame you are given. Ignore \
pets like cats and dogs. First, describe the scene you see accurately. Then,

Check:
- Are there any open doors in this frame?
- Are there any people in this frame?
- Are there any suspicious objects in this frame?
- Is the frame black or does it seem like the camera has been masked?
- Is there anything else that seems suspicious?

Only if none of the above is true, respond with "[ALL CLEAR]".
If you see something that's definitely suspicious, respond with "[RING ALARM]".
Ringing the alarm is an extremely expensive and serious action, so only do it \
if you are 100% certain that a security breach is happening.

Before answering, engage in an elaborate thinking process where you check all \
these points one by one. Talk to youself, do not rush."""

EXPLAIN_PROMPT = """You are a security guard.

You are monitoring a live video stream from a camera. Previously, you have \
identified something suspicious in the frame you are given. Now, your task is \
to explain briefly what's suspicious in the frame you are given. This message \
will be sent to the owners.

Accurately describe the scene you see in the frame. DO NOT ANSWER ANYTHING \
ELSE, no preamble, no greeting, no question at the end.

MAKE IT SHORT!"""


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


def prompt_model(frame, client):
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
                    "content": "Is there anything suspicious in this frame?",
                    "images": [frame],
                },
            ],
            stream=False,
        )["message"]["content"].strip()

        print("Model response:", answer)

        if "[RING ALARM]" in answer:
            return True
        elif "[ALL CLEAR]" in answer:
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

    while True:
        for stream in STREAMS:
            print("Downloading frame from", stream)

            url = stream_to_url(stream)
            frame = download_frame(url)

            if frame is None:
                print(f"Failed to download frame from {url}")
                continue

            print("Frame downloaded, prompting model...")
            if prompt_model(frame, client):
                print("Suspicious activity detected, explaining...")

                explanation = explain_danger(frame, client)
                ring_alarm(explanation)

                sleep(360)

        sleep(8)


def start_background_job():
    """
    Starts this guard service as a separate process.
    """

    process = Process(target=mainloop)
    process.start()

    return process
