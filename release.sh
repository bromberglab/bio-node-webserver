docker pull gcr.io/poised-cortex-254814/webservice-server:latest
docker tag gcr.io/poised-cortex-254814/webservice-server bromberglab/bio-node-webserver
docker push bromberglab/bio-node-webserver
docker pull gcr.io/poised-cortex-254814/webservice-client:latest
docker tag gcr.io/poised-cortex-254814/webservice-client bromberglab/bio-node-webclient
docker push bromberglab/bio-node-webclient
docker pull gcr.io/poised-cortex-254814/webservice-docs:latest
docker tag gcr.io/poised-cortex-254814/webservice-docs bromberglab/bio-node-docs
docker push bromberglab/bio-node-docs