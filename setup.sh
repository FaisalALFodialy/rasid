#!/bin/bash

# Install Chromium and ChromeDriver
apt-get update
apt-get install -y chromium chromium-driver

# Symlinks (very important)
ln -s /usr/bin/chromium /usr/bin/google-chrome
ln -s /usr/lib/chromium/chromedriver /usr/local/bin/chromedriver
