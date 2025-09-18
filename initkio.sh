#!/bin/bash
if [ ! -e /home/pi ]; then
    echo "Only run this on your pi."
    exit 1
fi
systemctl enable kiosk.service
systemctl disable firstboot.service
raspi-config --expand-rootfs > /dev/null
ipo=$(ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1 |  cut -d. -f2);
newHostname="rapi-kio6-"$ipo
hostnamectl set-hostname ${newHostname} --static

echo ${newHostname} > /etc/hostname
sed -i '/^127.0.0.1/s/.*/127.0.0.1\t'${newHostname}'/g' /etc/hosts
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf
echo '10.100.20.104   laiks.egl.local' >> /etc/hosts

echo "01 10 * * * sudo shutdown -r" >>  /var/spool/cron/crontabs/root
/sbin/shutdown -r now
