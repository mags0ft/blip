<p align="center">
  <img src="./app/static/images/blip-logo.webp" alt="blip logo" width="400">
</p>

# Blip

Blip is a small implementation of an AI-powered home security system.

> [!CAUTION]
> Blip is still a highly experimental beta and more of a proof-of-concept than a working production software.

Devices can be added to your local network - these can stream their camera feed to the local network by running a command like:

```bash
python3 ./app/device.py
```

The server needs to have Ollama installed and running. You can run the server with:

```bash
flask run
```

The model `qwen3-vl:4b` is used by default, but you can change this in the `.env` file. For example, some other/smaller Qwen VL models may be interesting to explore, but performance varies from use case to use case. Make sure to use a small and fast model, as you would otherwise waste even more electricity than you already do.

Make sure to also have set the `SECRET_KEY` environment variable to a random string:

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
