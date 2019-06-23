#!/bin/sh

set -e


sudo apt-get update
#sudo apt-get install python3-pip python3-virtualenv python3-ipython pigpio python3-pigpio
sudo apt-get install pigpio build-essential git-core

sudo systemctl enable pigpiod
sudo systemctl start pigpiod

wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh
bash Berryconda3-2.0.0-Linux-armv7l.sh

pip install apigpio aiohttp pyserial-asyncio async-timeout

echo "blacklist ipv6" >> /etc/modprobe.d/ipv6.conf

# pip install git+https://github.com/PierreRust/apigpio

reboot


# copy everything

# run ln -s /root/turngate/turngate.service /etc/systemd/system/turngate.service
# 