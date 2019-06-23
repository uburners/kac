# Generic Raspberry Pi preparation

- Get Raspberry Pi 3 Model B+
- Download and Flash DietPi
- Update dietpi.txt
  - Set AUTO_SETUP_NET_HOSTNAME=g2
  - AUTO_SETUP_SWAPFILE_SIZE=0
  - AUTO_SETUP_AUTOMATED=1
  - AUTO_SETUP_GLOBAL_PASSWORD=kurenivka123
  - AUTO_SETUP_SSH_SERVER_INDEX=-2
  - AUTO_SETUP_HEADLESS=1   
  - CONFIG_SERIAL_CONSOLE_ENABLE=0
  - CONFIG_ENABLE_IPV6=0
  - CONFIG_NTP_MIRROR=OpenWrt.lan
  - CONFIG_CHECK_DIETPI_UPDATES=0
- Boot DietPi, update
- Setup berryconda3 (https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh)



## Turngate RPi preparetion

- Prepare Raspberry Pi
- Copy dt-blob.bin to /boot/
- Copy code
- Convert DietPi to read-only filesystem
  - add `fastboot noswap ro fsck.mode=skip quiet` to `/boot/cmdline.txt`
  - run 
    rm -rf /var/lib/dhcp/
    ln -s /tmp /var/lib/dhcp
    rm -rf /var/run /var/spool /var/lock /var/tmp
    ln -s /tmp /var/run 
    ln -s /tmp /var/tmp
    ln -s /tmp /var/spool
    ln -s /tmp /var/lock

  - unlink /etc/resolv.conf && ln -s /etc/resolvconf/run/resolv.conf /etc/resolv.conf
  - mv /var/lib/dhcp /var/run/dhcp && ln -s /var/run/dhcp /var/lib/dhcp
  - rm -rf /var/lib/dhcpcd5 && ln -s /var/run /var/lib/dhcpcd5
  - rm -rf /var/db && mkdir -p /var/run/db && ln -s /var/run/db /var/db  
  - update fstab to mount all fs as ro  
- Reboot


## Access gateway preparation

- Prepare Raspberry Pi
- Convert DietPi to f2fs (see http://whitehorseplanet.org/gate/topics/documentation/public/howto_ext4_to_f2fs_root_partition_raspi.html)
- Copy code
- Reboot
