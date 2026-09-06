#!/bin/bash

echo "Updating ..."
git pull origin main

systemctl restart home-bot

echo "Done !"
