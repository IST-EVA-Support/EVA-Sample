#!/bin/sh

set -e

USER_PWD=${USER_PWD:=$PWD}
OUTPUT_DIR=${OUTPUT_DIR:=/opt/adlink/eva}
DIRS="samples bin"
SILENT=""

usage() {
    cat -<<EOF
Usage ./install.sh [-s] [-p INSTALL_DIR]

Option:
  s : Silent mode to install
  p : Package install directory
EOF
}

echo_exit() {
    echo;echo $@; echo; exit;
}

show_ascii_art() {
    cat -- <<EOF
*************************************************
  █████╗ ██████╗ ██╗     ██╗███╗   ██╗██╗  ██╗
  ██╔══██╗██╔══██╗██║     ██║████╗  ██║██║ ██╔╝
  ███████║██║  ██║██║     ██║██╔██╗ ██║█████╔╝
  ██╔══██║██║  ██║██║     ██║██║╚██╗██║██╔═██╗
  ██║  ██║██████╔╝███████╗██║██║ ╚████║██║  ██╗
  ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
*************************************************
EOF
}

license_confirm() {
    # Silent mode to install
    if [ ! -z "$SILENT" ]; then
        cat LICENSE
        return
    fi

    echo "Please read the EVA License Agreement carefully!"
    echo "Press Enter to continue ..."
    echo -n "(After press Enter, please press Q or q to quit.)"
    read tmp
    less LICENSE
    echo
    read -p "Do you agree to the EVA Free Software License Agreement? (y/n) " yn
    case $yn in
        [Yy]* ) ;;
        * ) echo_exit "Please enter Y or y to accept the EVA Free Software License Agreement."
    esac
}

ask_output() {
    if [ -z "$SILENT" ]; then
        read -p "Do you sure install EVA pacakge in ${OUTPUT_DIR}? (y/n)" yn
        case $yn in
            [Yy]* ) ;;
            * ) echo_exit "Please enter Y or y to continue install EVA package."
        esac
    fi

    [ -z "${OUTPUT_DIR##/*}" ] || OUTPUT_DIR="${USER_PWD}/${OUTPUT_DIR}"

    if [ -d ${OUTPUT_DIR} ]; then
        [ -w ${OUTPUT_DIR} ] || (echo "ERROR: Do not have write permission to ${OUTPUT_DIR}." && exit 1)
    else
        OLD_UMASK=$(umask)
        umask $(echo "755" | tr "01234567" "76543210")
        mkdir -m 755 -p ${OUTPUT_DIR} 2>/dev/null || (echo "ERROR: Create dir ${OUTPUT_DIR} failed, maybe do not have create permission." && exit 1)
        umask $OLD_UMASK
    fi
}

install_files() {
    echo "Install packages at \"${OUTPUT_DIR}\"."
    for d in $DIRS; do
        echo "Copying ${d}..."
        cp -a ${d} ${OUTPUT_DIR}
    done

    arch=$(uname -m)
    if [ "${arch}" = "x86_64" ]; then
        for d in $X86_64_DIRS; do
            echo "Copying X86_64 only ${d}..."
            cp -a ${d} ${OUTPUT_DIR}
        done
    fi
}

while getopts "hsp:" argv
do
    case $argv in
        s)
            SILENT=y
            ;;
        p)
            OUTPUT_DIR=$OPTARG
            ;;
        h|*)
            usage && exit
            ;;
    esac
done

show_ascii_art

license_confirm

ask_output

install_files
