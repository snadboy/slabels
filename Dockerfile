# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PLEX_URL=http://plex.snadboy.com
ENV PLEX_TOKEN=SxYYPquHSRe1NU9bwph1

ENV SONARR_URL=http://sonarr.snadboy.com
ENV SONARR_API_KEY=36261001e1ac41d185b42028228b8f09

ENV MAX_THREADS=5
ENV SYNC_INTERVAL_MINS=15

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /slabels
COPY . /slabels

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /slabels
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "app/log_config.ini"]
