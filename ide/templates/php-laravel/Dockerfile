# PHP-FPM service (Laravel-shaped starter). Composer deps install in a build
# stage; the php-fpm runtime stage filesystem is what the packer exports.
#
# This is a minimal, buildable PHP-FPM skeleton. To turn it into a full Laravel
# app, run `composer create-project laravel/laravel .` inside src/ from the IDE
# terminal, then adjust start.sh (artisan migrate, etc.) — see SERVICE_CONFIG_GUIDE.md.
FROM composer:2.7 AS composer
WORKDIR /app
COPY ./composer.json ./composer.json
RUN composer install --no-dev --no-scripts --no-interaction --prefer-dist || true
COPY ./src ./src

FROM php:8.3-fpm-alpine
RUN docker-php-ext-install pdo pdo_mysql mbstring bcmath
WORKDIR /var/www
COPY --from=composer /app/vendor ./vendor
COPY ./src /var/www
COPY ./start.sh /var/www/start.sh
RUN chmod +x /var/www/start.sh
