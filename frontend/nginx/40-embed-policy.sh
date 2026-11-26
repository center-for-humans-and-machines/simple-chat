#!/bin/sh
# Serve the chat page with the project's Content-Security-Policy frame-ancestors
# header (see "Allowed embedding origins" in the dashboard). nginx asks the
# backend at BACKEND_INTERNAL_URL for the policy on every page load.
# Without BACKEND_INTERNAL_URL the default nginx config is kept.
set -e

if [ -z "$BACKEND_INTERNAL_URL" ]; then
  echo "BACKEND_INTERNAL_URL not set: chat page served without frame-ancestors policy"
  exit 0
fi

cat >/etc/nginx/conf.d/default.conf <<CONF
server {
    listen 80;
    root /usr/share/nginx/html;

    location ~ ^/(index\.html)?$ {
        auth_request /_embed_policy;
        auth_request_set \$embed_policy \$upstream_http_content_security_policy;
        add_header Content-Security-Policy \$embed_policy always;
        try_files /index.html =404;
    }

    location = /_embed_policy {
        internal;
        proxy_pass ${BACKEND_INTERNAL_URL%/}/project/embed-policy;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI \$request_uri;
        proxy_ssl_server_name on;
    }

    location / {
        index index.html;
    }
}
CONF
