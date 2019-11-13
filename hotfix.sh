docker pull gcr.io/poised-cortex-254814/webservice-server:latest
docker build -f hotfix.dockerfile -t gcr.io/poised-cortex-254814/webservice-server .
docker push gcr.io/poised-cortex-254814/webservice-server:latest
kubectl delete pod -l "app=server"