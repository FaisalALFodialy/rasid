#!/bin/bash

# Install Chromium and Chromedriver
apt-get update
apt-get install -y chromium-browser chromium-chromedriver

# Link to expected locations
ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver
ln -s /usr/bin/chromium-browser /usr/bin/chrome
