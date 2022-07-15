Contents
=====
Most sensors connect to the Arduino nano (except for the GPS). The GPS and the Arduino
connect to the RaspberryPi via USB. There are udev rules on the rPi to get the device names set.

Checkout
=====
Suggest this be checked out on the rPi under /var as /var/www

Pre-requisites on the rPi
=====
apt-get install apache2 libapache2-mod-wsgi

```
cat > /etc/sudoers.d/020_www-data-nopasswd <<EOF
www-data ALL=(ALL) NOPASSWD: ALL
EOF
```
apt-get install gpsd
