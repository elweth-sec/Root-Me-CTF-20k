FROM php:7.4-apache

# Installation des extensions PHP nécessaires
RUN apt-get update \
    && apt-get install -y \
        libmagickwand-dev build-essential make wget curl --no-install-recommends \
    && pecl install imagick \
    && docker-php-ext-enable imagick

RUN docker-php-ext-install mysqli pdo pdo_mysql

# Copie des fichiers de configuration Apache
COPY config/php.ini /usr/local/etc/php/

# Installation de Imagick
COPY config/ImageMagick-7.1.0-49.tar.xz /tmp/
RUN tar -axvf /tmp/ImageMagick-7.1.0-49.tar.xz -C /tmp

# Changer de répertoire
WORKDIR /tmp/ImageMagick-7.1.0-49/

# Configurer et installer ImageMagick
RUN ./configure && \
    make install && \
    ldconfig /usr/local/lib

# Activation du module Apache mod_rewrite
RUN a2enmod rewrite

# Copie des fichiers du site dans le répertoire par défaut d'Apache
COPY src/ /var/www/html/

COPY ./flag.txt /flag-th3_Fl4g_1s_1nsId3.txt
RUN chmod 777 /flag-th3_Fl4g_1s_1nsId3.txt

RUN mkdir -p /var/www/html/uploads
RUN chmod 755 /var/www/html/uploads
RUN chown www-data:www-data /var/www/html/uploads 

# Donne les permissions nécessaires pour Apache
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html
