FROM python:3.9-slim

# Installation des dépendances système nécessaires à Electron
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libnotify4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libatspi2.0-0 \
    libsecret-1-0 \
    libasound2 \
    libappindicator3-1 \
    wget \
    curl \
    ncat \
    xvfb \
    dbus \
    dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Préparation X11 et dbus
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix \
    && mkdir -p /run/dbus && dbus-uuidgen > /etc/machine-id

# Installation de ton application Electron
COPY badge-creator_2.0.0_amd64.deb /tmp/
RUN dpkg -i /tmp/badge-creator_2.0.0_amd64.deb || apt-get install -f -y && \
    rm /tmp/badge-creator_2.0.0_amd64.deb

# Copie du flag
COPY flag.txt /flag.txt
RUN chmod 777 /flag.txt

# Configuration du répertoire de travail
WORKDIR /app
COPY web-app/ .

# Création d’un utilisateur non root
RUN useradd -ms /bin/bash developer && chown -R developer:developer /app
USER developer

# Installation des dépendances Python
ENV DISPLAY=:99
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Commande de lancement : démarre dbus, Xvfb, puis ton app Python
CMD ["sh", "-c", "dbus-daemon --session --fork && Xvfb :99 -screen 0 1024x768x24 & python app.py"]
