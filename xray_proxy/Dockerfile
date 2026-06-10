FROM alpine:3.20

ARG XRAY_VERSION=26.3.27

RUN apk add --no-cache curl unzip ca-certificates && \
    curl -fsSL -o /tmp/xray.zip \
      "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip" && \
    unzip -j /tmp/xray.zip xray -d /usr/local/bin && \
    chmod +x /usr/local/bin/xray && \
    rm -rf /tmp/xray.zip && \
    apk del curl unzip

EXPOSE 10808 10809

ENTRYPOINT ["/usr/local/bin/xray", "run", "-config", "/etc/xray/config.json"]
