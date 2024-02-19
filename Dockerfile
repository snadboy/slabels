# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PLEX_URL=http://plex.snadboy.com
ENV PLEX_TOKEN=SxYYPquHSRe1NU9bwph1

ENV SONARR_URL=http://sonarr.snadboy.com
ENV SONARR_API_KEY=36261001e1ac41d185b42028228b8f09

ENV MAX_THREADS=5
ENV SYNC_INTERVAL_MINS=15

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app
# COPY log_config.ini /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "--log-config", "log_config.ini", "app:app"]
