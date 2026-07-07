ARG BASE_IMAGE=egya-whisper-livekit-base:latest
FROM ${BASE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends libportaudio2 && rm -rf /var/lib/apt/lists/*