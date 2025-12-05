#!/bin/bash
systemctl enable kiosk.service;
systemctl disable firstboot.service;
raspi-config --expand-rootfs > /dev/null;
cp /etc/hosts /etc/hosts.backup;
oldHostname=$(cat /proc/sys/kernel/hostname);
ipo=$(ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1 |  cut -d. -f2);
newHostname="rapi-kiosk6DSI-${ipo}"
hostnamectl set-hostname ${newHostname} --static
# printf ${newHostname} > /etc/hostname
# sed -i '/^127.0.0.1/s/.*/127.0.0.1\t'${newHostname}'/g' /etc/hosts;
sed -i -e 's/'${oldHostname}'/'${newHostname}'/g' /etc/hosts;
sed -i '/^#NTP=.*/a FallbackNTP=laiks.egl.local' /etc/systemd/timesyncd.conf;
printf '10.100.20.104   laiks.egl.local\n' >> /etc/hosts;
printf '10.100.50.102   cache.egl.local\n' >> /etc/hosts;
printf "0 1 * * * /sbin/reboot \n" >>  /var/spool/cron/crontabs/root;
echo crontab -l
sleep 2
/sbin/shutdown -r now;
