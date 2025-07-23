#!/bin/bash

# Exit on any error
set -e

# Install Chromium and Chromedriver
apt-get update
apt-get install -y chromium chromium-driver

# Link chromium and chromedriver to expected locations
ln -s /usr/bin/chromium /usr/bin/chrome || true
ln -s /usr/lib/chromium/chromedriver /usr/bin/chromedriver || ln -s /usr/bin/chromedriver /usr/bin/chromedriver
