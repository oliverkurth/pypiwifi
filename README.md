# pypiwifi

This is a simple web interface that can control a wireless router based on a Raspberry Pi. It is
optimized to be used on a cell phone.

It makes a lot of assumptions on the configuration. At the momemt, the easiest way to use it is to create an
sd card image using this repository: https://github.com/oliverkurth/makepi and check out the pypiwifi
branch:

    sudo apt-get install qemu-user-static kpartx
    git clone https://github.com/oliverkurth/makepi.git
    git clone https://github.com/oliverkurth/pypiwifi.git
    git clone https://github.com/raspberrypi/firmware.git
    cd makepi
    git checkout pypiwifi
    sudo ./makepi.sh

