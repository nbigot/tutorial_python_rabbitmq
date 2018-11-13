FROM python:3.6-alpine
WORKDIR "/app"
COPY src ./src/
COPY config.yaml /app/config.yaml
RUN pip install --no-cache-dir -r ./src/requirements.txt
VOLUME /var/log/
STOPSIGNAL SIGINT
ENV PYTHONPATH "${PYTHONPATH}:/app/:/app/src/"
ENTRYPOINT ["python3", "-u", "/app/src/main.py", "--stdout", "-configfile", "/app/config.yaml"]
