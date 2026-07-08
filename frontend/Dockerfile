FROM nginx:alpine
COPY . /usr/share/nginx/html
COPY config.js.template /usr/share/nginx/html/config.js.template
RUN printf '#!/bin/sh\n: "${ASR_PORT:=8050}" "${STREAM_JUDGE_PORT:=8002}"\nexport ASR_PORT STREAM_JUDGE_PORT\nenvsubst < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js\n' > /docker-entrypoint.d/40-envsubst-config.sh && \
    chmod +x /docker-entrypoint.d/40-envsubst-config.sh
EXPOSE 80
