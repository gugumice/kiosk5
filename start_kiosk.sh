#!/usr/bin/env bash

cd /opt/kiosk
source .venv/bin/activate
sleep 2
startx /opt/kiosk/kiosk_main.py
