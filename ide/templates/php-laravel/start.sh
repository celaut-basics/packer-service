#!/bin/sh
set -e
# If this is a real Laravel app, run migrations before serving:
if [ -f /var/www/artisan ]; then
  php /var/www/artisan migrate --force || true
fi
exec php-fpm
