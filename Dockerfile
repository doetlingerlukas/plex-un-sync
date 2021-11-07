FROM python:3.10-alpine3.14

RUN apk update \
  && apk --no-cache add gcc \
  linux-headers \
  musl-dev \
  && pip install pipenv

COPY . /app
WORKDIR /app

RUN pipenv install --deploy --system --ignore-pipfile

ENTRYPOINT [ "python", "un-sync.py" ]
