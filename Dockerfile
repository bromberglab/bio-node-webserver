FROM yspreen/gcloudsdk-plus

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


ADD django webservice-key.json.enc setup.sh resize.sh requirements.txt .commit $APP_DIR/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apk del .build-deps

CMD [ "sh", "-c", "(/app/setup.sh; python /app/manage.py migrate; python /app/manage.py collectstatic --noinput; (sleep 48h; reboot) & python /app/manage.py daemon & daphne config.asgi:application -b 0.0.0.0 -p 8080) | multilog t s1048576 n5 /volume/logs/django"]
