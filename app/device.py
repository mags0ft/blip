#!/usr/bin/env python3

"""
Independent script to be executed on the devices with cameras.

Original author: Igor Maculan - n3wtron@gmail.com
A Simple MJPEG stream HTTP server

https://gist.github.com/n3wtron/4624820
"""


import cv2
from PIL import Image
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import io
import time

capture = None


class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-type",
            "multipart/x-mixed-replace; boundary=--BLIPBOUNDARY",
        )
        self.end_headers()

        while True:
            try:
                rc, img = capture.read()

                if not rc:
                    continue

                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                jpg = Image.fromarray(img_rgb)
                tmp_file = io.BytesIO()
                jpg.save(tmp_file, "JPEG")

                self.wfile.write(b"--BLIPBOUNDARY\r\n")
                self.send_header("Content-type", "image/jpeg")
                self.send_header(
                    "Content-length", str(tmp_file.getbuffer().nbytes)
                )

                self.end_headers()
                self.wfile.write(tmp_file.getvalue())
                time.sleep(1 / 30)

            except Exception as e:
                print("Streaming error:", e)
                break


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def main():
    global capture

    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(cv2.CAP_PROP_SATURATION, 1.0)

    try:
        server = ThreadedHTTPServer(("0.0.0.0", 8090), CamHandler)
        print("Starting server on port 8090...")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        capture.release()
        server.socket.close()


if __name__ == "__main__":
    main()
