#!/bin/bash
set -e

apt-get update
apt-get install -y chromium-driver chromium

# روابط للمسارات المتوقعة من Selenium
ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver
ln -sf /usr/bin/chromium /usr/bin/google-chrome
