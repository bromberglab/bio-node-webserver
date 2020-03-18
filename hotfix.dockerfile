FROM gcr.io/poised-cortex-254814/webservice-server:latest

ADD django $APP_DIR/
ADD resize.sh $APP_DIR/resize.sh