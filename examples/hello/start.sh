#!/bin/sh
# Tiny TCP echo on :8080 so the packed service is actually runnable.
exec httpd -f -p 8080 -h /app
