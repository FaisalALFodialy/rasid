#!/bin/bash

# Install Chromium
apt-get update
apt-get install -y chromium-browser chromium-chromedriver

# Create symlinks so selenium can find Chrome and Chromedriver
ln -s /usr/bin/chromium-browser /usr/bin/google-chrome
ln -s /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver
