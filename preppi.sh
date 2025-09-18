#!/bin/bash

USER="pi"
GROUP="kiosk"
WORK_DIR="/opt/kiosk/"
USER_DIR="/home/pi/"

apt-get update && apt-get upgrade -y
# Disable bluetooth & WiFi
systemctl disable bluetooth.service
systemctl disable hciuart.service

# ln /opt/kiosk/kiosk.service /lib/systemd/system/kiosk.service
# ln /opt/kiosk/firstboot.service /lib/systemd/system/firstboot.service
# ln /opt/kiosk/kiosk.ini /home/pi/kiosk.ini
# systemctl enable firstboot.service
printf "Setting timezone & logs"
timedatectl set-timezone Europe/Riga
sed -i '/^# Additional overlays.*/a dtoverlay=pi3-disable-wifi\ndtoverlay=pi3-disable-bt' /boot/config.txt
sed -i '/^\[all\].*/a gpu_mem=256' /boot/firmware/config.txt
printf "Setting logfiles" 

file_path="/var/log/kiosk/kiosk.log"
if ! mkdir -p /var/log/kiosk; then
    printf "Error: Failed to create file directory" >&2
fi

if ! touch "${file_path}"; then
    printf "Error: Failed to create file %s\n" "$file_path" >&2
fi
if ! chown "${OWNER}:${GROUP}" "$file_path"; then
    printf "Error: Failed to set ownership to %s:%s for file %s\n" "$owner" "$group" "$file_path" >&2
fi
ln -s "${file_path}" /home/pi/kiosk.log

printf "Config watchdog"
addgroup watchdog
usermod -a -G watchdog "${USER}"
printf'KERNEL=="watchdog", MODE="0660", GROUP="watchdog"' > /etc/udev/rules.d/60-watchdog.rules 

printf "Config hosts"
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf
printf '10.100.20.104   laiks.egl.local' >> /etc/hosts
printf "Setting touchoad"
source touchpad_rules.sh

printf "Setting PIP"
apt-get --yes install python3-pip
sed -i '/^\[global\]$/a break-system-packages = true' /etc/pip.conf

printf "Install & configure CUPS"

apt-get --yes install libcups2-dev cups cups-bsd -y
cupsctl --remote-admin --remote-any
usermod -a -G lpadmin $USER
usermod -a -G lp $USER
#Disable CUPS-browsed
source change_cups-browsed.sh
service cups restart

printf "Install tkinter & stuff"

sudo apt-get install xserver-xorg -y
sudo apt-get install xinit -y
sudo apt-get install x11-xserver-utils -y

sudo apt install raspberrypi-ui-mods -y
sudo apt-get install python3-tk -y

printf "Installing venv"

pip3 install pyserial
sudo apt install python3-venv -y
python3 -m venv --system-site-packages "${WORK_DIR}.venv"
source .venv/bin/activate
pip3 install customtkinter
pip3 install pillow

printf "Install screen brightness utility"
cd "${USER_DIR}"

wget https://files.waveshare.com/wiki/common/Brightness.zip
unzip "${USER_DIR}Brightness.zip"
chmod a+x "${USER_DIR}Brightness/install.sh"
source "${USER_DIR}Brightness/install.sh"
rm -r "${USER_DIR}Brightness"


#/usr/sbin/shutdown -r now
