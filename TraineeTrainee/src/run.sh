#!/bin/bash

# Démarrer Flask en arrière-plan
python3 /app/app.py &

# Démarrer Nginx
/usr/local/nginx/sbin/nginx -g "daemon off;"
