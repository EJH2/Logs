FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
WORKDIR /srv/
COPY . /srv/
RUN apk update && apk add bash postgresql-dev gcc python3-dev musl-dev
RUN pip install -r ./requirements.txt
RUN python setup.py install
EXPOSE 80
