#FROM ubuntu:latest
FROM python:2.7-alpine
#RUN apt-get update -y
#RUN apt-get install -y python-pip python-dev build-essential
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["download_count.py"]