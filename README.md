# Blip

Blip is a small implementation of an AI-powered home security system.

Devices can be added to your local network - these can stream their camera feed to the local network by running a command like:

```bash
python3 ./app/device.py
```

The server needs to have Ollama installed and running. You can run the server with:

```bash
flask run
```

Make sure to have set the `SECRET_KEY` environment variable to a random string:

```bash
# Generate a key, make sure to copy it and keep it secret!
openssl rand -hex 32

# Create a .env file
cp .env.example .env

# Edit the .env file to set your SECRET_KEY
nano .env
```

You can then access the web interface at `http://localhost:5000`.

Any camera devices need to be added to the `STREAMS` constant in `config.py`.
