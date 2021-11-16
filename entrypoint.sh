#!/bin/sh

set -e

if ! [[ -f /secrets/id_rsa ]]; then
  echo "Required ssh key not found!"
fi

cp /secrets/id_rsa ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

python un-sync.py
