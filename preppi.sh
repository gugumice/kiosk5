#!/bin/bash

USER="pi"
GROUP="kiosk"
WORK_DIR="/opt/kiosk/"
USER_DIR="/home/pi/"
# Disable bluetooth & WiFi
systemctl disable bluetooth.service
systemctl disable hciuart.service

printf "Install tkinter & stuff\n"
apt-get update
apt-get install xserver-xorg -y
apt-get install xinit -y
apt-get install x11-xserver-utils -y
#apt install raspberrypi-ui-mods -y
apt-get install python3-tk -y

printf "Changing Xwrapper.config\n"
sed -i 's/^allowed_users=console$/allowed_users=anybody/' /etc/X11/Xwrapper.config

ln /opt/kiosk/kiosk.service /lib/systemd/system/kiosk.service
ln /opt/kiosk/firstboot.service /lib/systemd/system/firstboot.service
ln /opt/kiosk/kiosk.ini /home/pi/kiosk.ini
systemctl enable firstboot.service

printf "Setting timezone & logs\n"
timedatectl set-timezone Europe/Riga
printf "Setting logfiles\n" 
./make_logdirs.sh "/var/log/kiosk/kiosk.log"
ln -s "${file_path}" /home/pi/kiosk.log

printf "Updating config.sys\n"
./update_config.sh "/boot/firmware/config.txt"

printf "Config watchdog\n"
addgroup watchdog
usermod -aG watchdog "${USER}"
printf 'KERNEL=="watchdog", MODE="0660", OWNER="pi", GROUP="watchdog"\n' > /etc/udev/rules.d/60-watchdog.rules
# chown pi:kiosk /dev/watchdog

printf "Setting touchoad\n"
./touchpad_rules.sh

printf "Setting PIP\n"
apt-get install python3-pip -y
####
apt-get install python3-pil.imagetk -y
sed -i '/^\[global\]$/a break-system-packages = true' /etc/pip.conf

printf "Install & configure CUPS\n"
sleep 2
# 32 bit
apt-get install gcc python3-dev libcups2-dev cups cups-bsd -y
#64 bit
apt-get install libcups2-dev cups cups-bsd -y
sleep 1
cupsctl --remote-admin --remote-any
usermod -aG lpadmin $USER
usermod -aG lp $USER
#Disable CUPS-browsed
./change_cups-browsed.sh
sleep 1
service cups restart

printf "Installing venv\n"
apt install python3-venv -y
python3 -m venv --system-site-packages "${WORK_DIR}.venv"
source .venv/bin/activate
pip3 install customtkinter
pip3 install pillow
pip3 install pyserial
pip3 --no-input install pycups

printf "Install screen brightness utility\n"
cd "${USER_DIR}"

wget https://files.waveshare.com/wiki/common/Brightness.zip
# echo 127 |tee /sys/class/backlight/*/brightness
unzip "${USER_DIR}Brightness.zip"
chmod a+x "${USER_DIR}Brightness/install.sh"
source "${USER_DIR}Brightness/install.sh"
rm -r "${USER_DIR}Brightness"
#/usr/sbin/shutdown -r now
