#!/bin/bash

set -ex

VERSION="$(git describe --tags 2>&1 || true)"

TMP_DIR="${TMP_DIR:=_build}"

SAMBA_USERNAME="${SAMBA_USERNAME:=eva}"
SAMBA_PASSWORD="${SAMBA_PASSWORD:=eva}"
SAMBA_BASE_RELEASE_URL="${SAMBA_BASE_URL:=172.30.80.83/EVA_Release/releases}"
SAMBA_FULL_URL="ftp://${SAMBA_USERNAME}:${SAMBA_PASSWORD}@${SAMBA_BASE_RELEASE_URL}"

rm -rf ${TMP_DIR} || true
mkdir ${TMP_DIR}

base_copy() {
    local dst=$1

    [ -d $dst ] || mkdir $dst

    echo "$VERSION" > $dst/VERSION

    cp LICENSE $dst

    cp -r samples $dst

    cp setups/install.sh $dst

    mkdir $dst/bin
}

copy_linux_x86() {
    local dst="${TMP_DIR}/linux_x86"
    echo "Copy linux x86 files into $dst"

    base_copy $dst

    curl ${SAMBA_FULL_URL}/EVA_IDE/EVA_IDE-x86_64-linux -o $dst/bin/EVA_IDE
    chmod +x $dst/bin/EVA_IDE
}

copy_linux_aarch64() {
    local dst="${TMP_DIR}/linux_aarch64"
    echo "Copy linux aarch64 files into $dst"

    base_copy $dst

    curl ${SAMBA_FULL_URL}/EVA_IDE/EVA_IDE-aarch64-linux -o $dst/bin/EVA_IDE
    chmod +x $dst/bin/EVA_IDE
}

copy_windows() {
    local dst="${TMP_DIR}/windows"
    echo "Copy windows files into $dst"

    base_copy $dst

    curl ${SAMBA_FULL_URL}/EVA_IDE/EVA_IDE-x86_64-windows.exe -o $dst/bin/EVA_IDE
    chmod +x $dst/bin/EVA_IDE
}

echo "Copy EVA-Samples version ${VERSION}"

copy_linux_x86

copy_linux_aarch64

copy_windows
