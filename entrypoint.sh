#!/bin/sh

set -e

if ! [[ -f /secrets/id_rsa ]]; then
  echo "Required ssh key not found."
  exit
fi

cp /secrets/id_rsa ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

if [[ -z "${SCHEDULE}" ]]; then
  echo "No schedule provided. Sync will now run once and container will exit."
  python un-sync.py
  exit
fi

echo "jobs:
  - name: un-sync
    command: python /app/un-sync.py
    schedule: \"${SCHEDULE}\"
" > ~/crontab.yml

yacron -c ~/crontab.yml
