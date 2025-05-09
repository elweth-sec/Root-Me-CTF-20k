FROM debian:bullseye

# Installation des dépendances pour Nginx et Python
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpcre3 \
    libpcre3-dev \
    zlib1g \
    zlib1g-dev \
    libssl-dev \
    python3 \
    python3-pip \
    ncat \
    && rm -rf /var/lib/apt/lists/*

# Téléchargement et compilation de Nginx avec le module custom
RUN curl -sL https://nginx.org/download/nginx-1.24.0.tar.gz | tar xz -C /usr/local/src

# Copier le code du module custom "root-me-backdoor" dans le conteneur
COPY ./root-me-backdoor /usr/local/src/root-me-backdoor

# Configuration et compilation de Nginx avec le module
WORKDIR /usr/local/src/nginx-1.24.0
RUN ./configure \
    --prefix=/usr/local/nginx \
    --conf-path=/etc/nginx/nginx.conf \
    --with-compat \
    --with-http_ssl_module \
    --add-module=/usr/local/src/root-me-backdoor \
    && make \
    && make install

# Installation des dépendances Python
COPY app/requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copier le code de l'application
COPY app/ /app

# Copier le fichier de configuration Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copie du script de démarrage et du fichier flag
COPY run.sh /run.sh
RUN chmod +x /run.sh

COPY flag-9fb215456edeadc855c755846be83cc310a5d262aa5d9360dd27db9cd0141a9d /flag-9fb215456edeadc855c755846be83cc310a5d262aa5d9360dd27db9cd0141a9d
RUN chmod 777 /flag-9fb215456edeadc855c755846be83cc310a5d262aa5d9360dd27db9cd0141a9d

# Exposer les ports nécessaires
EXPOSE 80 5000

# Lancer le script de démarrage
CMD ["/run.sh"]
