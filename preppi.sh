#!/bin/bash

USER="pi"
GROUP="kiosk"
WORK_DIR="/opt/kiosk/"
USER_DIR="/home/pi/"

apt-get update && apt-get upgrade -y
# Disable bluetooth & WiFi
systemctl disable bluetooth.service
systemctl disable hciuart.service

ln /opt/kiosk/kiosk.service /lib/systemd/system/kiosk.service
ln /opt/kiosk/firstboot.service /lib/systemd/system/firstboot.service
ln /opt/kiosk/kiosk.ini /home/pi/kiosk.ini
systemctl enable firstboot.service

printf "Setting timezone & logs"
timedatectl set-timezone Europe/Riga
printf "Setting logfiles" 
./make_logdirs.sh "/var/log/kiosk/kiosk.log"
ln -s "${file_path}" /home/pi/kiosk.log

printf "Updating config.sys"
./update_config.sh "/boot/firmware/config.txt"

printf "Config watchdog"
addgroup watchdog
usermod -a -G watchdog "${USER}"
printf'KERNEL=="watchdog", MODE="0660", GROUP="watchdog"' > /etc/udev/rules.d/60-watchdog.rules 

printf "Setting touchoad"
./touchpad_rules.sh

printf "Setting PIP"
apt-get --yes install python3-pip
sed -i '/^\[global\]$/a break-system-packages = true' /etc/pip.conf

printf "Install & configure CUPS"

apt-get --yes install libcups2-dev cups cups-bsd -y
cupsctl --remote-admin --remote-any
usermod -a -G lpadmin $USER
usermod -a -G lp $USER
#Disable CUPS-browsed
./change_cups-browsed.sh
sleep 2
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
# echo 127 | sudo tee /sys/class/backlight/*/brightness
unzip "${USER_DIR}Brightness.zip"
chmod a+x "${USER_DIR}Brightness/install.sh"
source "${USER_DIR}Brightness/install.sh"
rm -r "${USER_DIR}Brightness"

#/usr/sbin/shutdown -r now
