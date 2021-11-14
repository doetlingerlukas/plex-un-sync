FROM python:3.9-alpine3.14

RUN apk update \
  && apk --no-cache add gcc \
  linux-headers \
  musl-dev \
  openssh-client \
  sshpass \
  && pip install pipenv

COPY . /app
WORKDIR /app

RUN addgroup -S group && adduser -S user -G group
RUN mkdir -p /home/user/.ssh
RUN printf "Host *\n\tStrictHostKeyChecking no\n" >> /home/user/.ssh/config

COPY id_rsa /home/user/.ssh/id_rsa

RUN chown -R user:group /home/user/.ssh
RUN chmod 600 /home/user/.ssh/id_rsa

USER user

RUN pipenv install --deploy --system --ignore-pipfile

ENTRYPOINT [ "python", "un-sync.py" ]
