Contents
=====
Most sensors connect to the Arduino nano (except for the GPS). The Arduino
connects to the RaspberryPi/Beaglebone via a UART on the computer. Baud setting
must match between the units.

Checkout
=====
Suggest this be checked out under /var as /var/www

Pre-requisites
=====
apt-get install apache2 libapache2-mod-wsgi

add to /etc/apache2/mods-available/wsgi.conf:

    WSGIScriptAlias /wsgi/  /var/www/wsgi/
    WSGIScriptAlias /pickle /var/www/wsgi/pickle.wsgi

cat > /etc/sudoers.d/020_www-data-nopasswd <<EOF
www-data ALL=(ALL) NOPASSWD: ALL
EOF

apt-get install gpsd
