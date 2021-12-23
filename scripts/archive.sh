#!/bin/bash

set -e

DIR=$(cd $(dirname $0) && pwd)
TMP_DIR="${TMP_DIR:=_build}"

cd $TMP_DIR

${DIR}/makeself linux_x86 EVA-Samples_x86_64-linux-gnu.run "Adlink EVA Samples Software Package" ./install.sh
${DIR}/makeself linux_aarch64 EVA-Samples_aarch64-linux-gnu.run "Adlink EVA Samples Software Package" ./install.sh

cd windows
zip EVA-Samples_x86_64-windows.zip -r *
mv EVA-Samples_x86_64-windows.zip ..
cd -
