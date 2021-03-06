#!/bin/bash

set -ex

VERSION="$(git describe --tags 2>/dev/null || true)"

SAMBA_USERNAME="${SAMBA_USERNAME:=eva}"
SAMBA_PASSWORD="${SAMBA_PASSWORD:=eva}"
SAMBA_SAMPLES_RELEASE_URL="${SAMBA_BASE_URL:=172.30.80.83/EVA_Release/releases/EVA-Samples}"
SAMBA_FULL_URL="ftp://${SAMBA_USERNAME}:${SAMBA_PASSWORD}@${SAMBA_SAMPLES_RELEASE_URL}"

TMP_DIR="${TMP_DIR:=_build}"

cd $TMP_DIR

if [ -z "VERSION" ]; then
    BASE_NAME=EVA_IDE
else
    BASE_NAME=EVA_IDE_${VERSION}
    echo -en ${VERSION} > latest_version
fi

curl -T EVA-Samples_x86_64-linux-gnu.run ${SAMBA_FULL_URL}/${BASE_NAME}_x86_64-linux-gnu.run
curl -T EVA-Samples_aarch64-linux-gnu.run ${SAMBA_FULL_URL}/${BASE_NAME}_aarch64-linux-gnu.run
curl -T EVA-Samples_x86_64-windows.zip ${SAMBA_FULL_URL}/${BASE_NAME}_x86_64-windows.zip
curl -T latest_version ${SAMBA_FULL_URL}/latest_version
