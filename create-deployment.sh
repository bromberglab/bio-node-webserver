#!/bin/sh

# paths
export proj="$(pwd)"
export kubeconfigs="$proj/kube_configs"
export path="$(cd; pwd)"

# versions
export usernetesversion="v20191203.0"
export helmversion="v3.0.2"

# variables
export mainstoragesize="100Gi"
export nfsstoragesize="90Gi"
export mainstoragepath="$path/mnt"


# prevent nginx conf subst
export host='$host'
export request_uri='$request_uri'
export http_x_forwarded_proto='$http_x_forwarded_proto'
export http_x_forwarded_for='$http_x_forwarded_for'

random_string()
{
    cat /dev/urandom | base64 | fold -w ${1:-10} | head -n 1 | sed -e 's/[\/\+]/a/g'
}

apply_subst() {
    f="$1"

    cat "$f" | envsubst > apply.yml
    kubectl apply -f apply.yml
    rm apply.yml
}
print_apply_subst() {
    f="$1"

    cat "$f" | envsubst
}

helm_subst() {
    f="$1"
    shift

    cat "$f" | envsubst > helm.yml
    helm install "$@" -f helm.yml
    rm helm.yml
}

make_secret() {
    val="$(printf "$(random_string 32)" | base64)"
    echo "  $1: \"$val\"" >> secret.yml
}

secretvalues="
encryption_key
db_pw
db_host
gs_secret
sendgrid_key
sendgrid_sender
"

mkdir "$mainstoragepath"
which bzip2>/dev/null || sudo yum install -y bzip2 || return
which gzip>/dev/null || sudo yum install -y gzip || return

cd $path
curl -o usernetes-x86_64.tbz --location "https://github.com/rootless-containers/usernetes/releases/download/$usernetesversion/usernetes-x86_64.tbz"
tar xjf usernetes-x86_64.tbz
rm usernetes-x86_64.tbz
cd usernetes
./run.sh 1> "./log.txt" 2> "./err.txt" &
sleep 4

# kustomize disabled
# curl -o kustomize --location https://github.com/kubernetes-sigs/kustomize/releases/download/v3.1.0/kustomize_3.1.0_linux_amd64
# chmod u+x ./kustomize

mkdir helmdir
cd helmdir
curl -o helm.tgz --location "https://get.helm.sh/helm-$helmversion-linux-amd64.tar.gz"
tar xzf helm.tgz
rm helm.tgz
cd *
mv helm ../../
cd ../..
rm -rf helmdir

# either
echo "alias kubectl='$path/usernetes/kubectl.sh'" >> ~/.bashrc
# or
# sudo yum install -y kubectl

# kustomize disabled
# echo "alias kustomize='$path/usernetes/kustomize'" >> ~/.bashrc

echo "alias helm='$path/usernetes/helm'" >> ~/.bashrc
echo "$path/usernetes/rootlessctl.sh add-ports 127.0.0.1:8080:8080/tcp >/dev/null 2>&1" >> ~/.bashrc
echo "export KUBECONFIG='$path/usernetes/config/localhost.kubeconfig'" >> ~/.bashrc
. ~/.bashrc

helm repo add stable https://kubernetes-charts.storage.googleapis.com/

curl -o dns.yml https://storage.googleapis.com/kubernetes-the-hard-way/coredns.yaml
sed -Ei 's/clusterIP:.*$/clusterIP: 10.0.0.10/' dns.yml
kubectl apply -f dns.yml

export nodename="$(kubectl get nodes -o name | tail -1 | sed 's/node\///')"


cd $kubeconfigs

[ -f secret.yml ] || echo "apiVersion: v1
kind: Secret
metadata:
  name: secrets-config
data:" > secret.yml

echo "$secretvalues" | while read l
do
    if ! [ "$l" = "" ]
    then
        grep "$l": secret.yml >/dev/null || make_secret "$l"
    fi
done


kubectl apply -f $kubeconfigs/secret.yml
helm_subst $kubeconfigs/storage/helm-config.yml nfs-release stable/nfs-server-provisioner
sleep 5
export nfspvcname="$(kubectl get persistentvolumeclaim -o name | grep nfs-release | sed 's/persistentvolumeclaim\///')"
apply_subst $kubeconfigs/storage/classes.yml
sleep 5
apply_subst $kubeconfigs/storage/pvc.yml


echo "waiting for nfs to start ..."; sleep 15
kubectl apply -f $kubeconfigs/storage/pvc.yml
echo "waiting for pvc ..."; sleep 5

kubectl apply -f $kubeconfigs/deployment.yml
echo "waiting for server to start ..."; sleep 30
kubectl apply -f $kubeconfigs/ingress.yml
kubectl apply -f $kubeconfigs/dist.yml
echo "waiting for dist copy ..."; sleep 15
kubectl delete -f $kubeconfigs/dist.yml
echo "done. ingress may need ~5min to boot."

# [ -f gs_secret.txt ] || LC_ALL=C tr -dc "A-Za-z0-9-_" </dev/urandom | head -c 20 > gs_secret.txt
# echo "gs_secret: $(cat gs_secret.txt | tr -d '\n' | base64)"
# gsutil notification watchbucket -t "$(cat gs_secret.txt)" https://bio-no.de/webhooks/gs_update/ gs://artifacts.poised-cortex-254814.appspot.com
