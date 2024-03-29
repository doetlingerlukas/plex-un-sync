FROM python:3.9-alpine3.14

RUN apk update \
  && apk --no-cache add gcc \
  linux-headers \
  musl-dev \
  openssh-client \
  sshpass \
  rsync \
  tzdata \
  && pip install pipenv \
  yacron

COPY . /app
WORKDIR /app

ENV TZ=Europe/Vienna
RUN cp /usr/share/zoneinfo/$TZ /etc/localtime

RUN addgroup -S group && adduser -S user -G group
RUN mkdir -p /home/user/.ssh
RUN printf "Host *\n\tStrictHostKeyChecking no\n" >> /home/user/.ssh/config

RUN chown -R user:group /home/user/.ssh

USER user

RUN pipenv install --deploy --system --ignore-pipfile

ENTRYPOINT [ "/bin/sh", "entrypoint.sh" ]
