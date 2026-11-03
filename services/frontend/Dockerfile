
FROM nginxinc/nginx-unprivileged:stable-alpine

# Temporarily switch to root to update system packages
USER root
RUN apk upgrade --no-cache

# Switch back to the unprivileged NGINX user
USER 101

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 8080
