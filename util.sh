openssl aes-256-cbc -K "$encryption_key" -iv "$encryption_key"2 -in webservice-key.json -out webservice-key.json.enc

docker build . -f sdk.Dockerfile -t gsdk
docker tag gsdk yspreen/gcloudsdk-plus
docker push yspreen/gcloudsdk-plus

docker system prune -a
