FROM python:3.8-slim

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

COPY invite0 /invite0
WORKDIR /

EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "invite0:app"]
