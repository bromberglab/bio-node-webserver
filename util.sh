docker build . -f sdk.Dockerfile -t gsdk
docker tag gsdk yspreen/gcloudsdk-plus
docker push yspreen/gcloudsdk-plus

docker system prune -a
