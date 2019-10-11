FROM gcr.io/poised-cortex-254814/cloudsdk

ENV APP_DIR=/app

RUN mkdir $APP_DIR
WORKDIR $APP_DIR

RUN pip install --upgrade pip

ADD django $APP_DIR/
ADD webservice-key.json.enc $APP_DIR/
ADD inspect.sh $APP_DIR/
RUN chmod +x inspect.sh
ADD requirements.txt $APP_DIR/
RUN pip install -r requirements.txt
