FROM gcr.io/poised-cortex-254814/cloudsdk

ENV APP_DIR=/app

RUN mkdir $APP_DIR && \
    apk update && \
    apk upgrade && \
    apk add --no-cache --virtual .build-deps \
    gcc \
    libc-dev \
    libffi-dev \
    openssl-dev
WORKDIR $APP_DIR


ADD django webservice-key.json.enc setup.sh inspect.sh requirements.txt .commit $APP_DIR/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    chmod +x inspect.sh && \
    apk del .build-deps
