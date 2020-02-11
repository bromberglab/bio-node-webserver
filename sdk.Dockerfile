FROM docker:17.12.0-ce as static-docker-source

RUN cd /usr/local/bin/ \
    && wget https://github.com/lukas2511/alpine-docker-images/raw/master/parts/tools/daemontools/files/command/multilog \
    && wget https://github.com/lukas2511/alpine-docker-images/raw/master/parts/tools/daemontools/files/command/tai64nlocal \
    && chmod +x multilog \
    && chmod +x tai64nlocal \
    && cd

FROM python:3.7-alpine
ARG CLOUD_SDK_VERSION=280.0.0
ENV CLOUD_SDK_VERSION=$CLOUD_SDK_VERSION

ENV PATH /google-cloud-sdk/bin:$PATH
COPY --from=static-docker-source /usr/local/bin/docker /usr/local/bin/multilog /usr/local/bin/tai64nlocal /usr/local/bin/
RUN apk --no-cache add \
    curl \
    py-crcmod \
    libc6-compat \
    openssh-client \
    git \
    gnupg \
    openssl \
    jq \
    postgresql-client \
    redis \
    && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    gcloud components update && \
    gcloud components update kubectl && \
    gcloud config set core/disable_usage_reporting true && \
    gcloud config set component_manager/disable_update_check true && \
    gcloud config set metrics/environment github_docker_image && \
    gcloud --version

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir psycopg2-binary==2.8.3 \
    && apk del --no-cache .build-deps
