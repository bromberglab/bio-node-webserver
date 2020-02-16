#!/bin/sh

# DEFAULTS for all settings:
ZONENAME="us-east1-a"
CLUSTERNAME="bio-node-cluster"
SANAME="bio-node-sa"
helmversion="v3.0.2"
PROJECTNAME='$fromgcloud'
DBSIZE="10Gi"
VOLUMESIZEPERNODE="1000Gi"
VOLUMEMETASIZEPERNODE="10Gi"
STORAGENODES="3"
MAXNODES="9"
MACHINETYPE="n1-standard-8"

[ -d /usr/local/opt/gettext/bin ] && export PATH="/usr/local/opt/gettext/bin:$PATH"

load_settings() {
    [ -f .bio-node.config ] && source .bio-node.config && rm .bio-node.config
    for setting in ZONENAME CLUSTERNAME PROJECTNAME SANAME DBSIZE VOLUMESIZEPERNODE VOLUMEMETASIZEPERNODE STORAGENODES MAXNODES MACHINETYPE
    do
        echo "export $setting="\""$(eval 'echo $'$setting)"\" >> .bio-node.config
    done
    source .bio-node.config
}

random_string()
{
    cat /dev/urandom | base64 | fold -w ${1:-10} | head -n 1 | sed -e 's/[\/\+]/a/g'
}

apply_subst() {
    f="$1"

    cat "$f" | envsubst > .apply.yml
    kubectl apply -f .apply.yml
    rm .apply.yml
}
print_apply_subst() {
    f="$1"

    cat "$f" | envsubst
}

helm_subst() {
    f="$1"
    shift

    cat "$f" | envsubst > .helm.yml
    $helm install "$@" -f .helm.yml
    rm .helm.yml
}

make_secret() {
    if [ $# -eq 1 ]
    then
        val="$(random_string 32)"
    else
        val="$2"
    fi
    val="$(printf "$val" | base64)"
    echo "  $1: \"$val\"" >> secret.yml
}

new_account() {
    echo | gcloud iam service-accounts delete \
      ${SANAME}@${PROJECTNAME}.iam.gserviceaccount.com
    gcloud iam service-accounts create ${SANAME} \
      --description "Service account that is used by Bio-Node to manage the cluster." \
      --display-name "Bio-Node SA"
    gcloud projects add-iam-policy-binding ${PROJECTNAME} \
      --member serviceAccount:${SANAME}@${PROJECTNAME}.iam.gserviceaccount.com \
      --role roles/editor
    gcloud projects add-iam-policy-binding ${PROJECTNAME} \
      --member serviceAccount:${SANAME}@${PROJECTNAME}.iam.gserviceaccount.com \
      --role roles/storage.admin
    gcloud projects add-iam-policy-binding ${PROJECTNAME} \
      --member serviceAccount:${SANAME}@${PROJECTNAME}.iam.gserviceaccount.com \
      --role roles/container.admin
    gcloud iam service-accounts keys create sa-key.json \
      --iam-account ${SANAME}@${PROJECTNAME}.iam.gserviceaccount.com
}

sa_secret() {
    kubectl delete secret sa-key
    kubectl create secret generic sa-key --from-file=./sa-key.json
    # rm ./sa-key.json
}

install_helm() {
    mkdir helmdir
    cd helmdir
    curl -o helm.tgz --location "https://get.helm.sh/helm-$helmversion-linux-amd64.tar.gz"
    tar xzf helm.tgz
    rm helm.tgz
    cd *
    mv helm ../../
    cd ../..
    rm -rf helmdir
}

requirements() {
    for r in curl tar gcloud kubectl envsubst
    do
        if [ "$(which "$r")" = "" ]
        then
            echo "Requirement missing: $r"
            if [ $r = envsubst ]
            then
                echo "On macOS: brew install gettext"
            fi
            return 1
        fi
    done
}

new_cluster() {
    gcloud container clusters create $CLUSTERNAME --image-type ubuntu --machine-type $MACHINETYPE --num-nodes $STORAGENODES
}

main() {
    requirements || return 1

    if [ "$PROJECTNAME" = '$fromgcloud' ]
    then
        PROJECTNAME="$(gcloud info | grep project | sed -E 's/^.* (.*)$/\1/g' | sed -E 's/(\[|\])//g')"
    fi
    load_settings

    if which helm>/dev/null
    then
        helm="helm"
    else
        if ! [ -f helm ]
        then
            install_helm
        fi
        helm="./helm"
    fi

    rm sa-key.json
    new_account
    sa_secret
    new_cluster

    gcloud container clusters get-credentials $CLUSTERNAME --zone $ZONENAME --project $PROJECTNAME
    gcloud compute addresses create server-address --global

    helm repo add stable https://kubernetes-charts.storage.googleapis.com/

    cd kube_configs
    secretvalues="
    db_pw
    sendgrid_key
    sendgrid_sender
    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD
    "
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
    grep "projectname": secret.yml >/dev/null || make_secret "projectname" "$PROJECTNAME"
    grep "zonename": secret.yml >/dev/null || make_secret "zonename" "$ZONENAME"
    grep "clustername": secret.yml >/dev/null || make_secret "clustername" "$CLUSTERNAME"
    grep "minnodes": secret.yml >/dev/null || make_secret "minnodes" "$STORAGENODES"
    grep "maxnodes": secret.yml >/dev/null || make_secret "maxnodes" "$MAXNODES"


    kubectl apply -f secret.yml
    kubectl apply -f storage/gce.yml
    kubectl apply -f priority.yml
    apply_subst db.yml

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
    kubectl apply -f kube_configs/ingress.yml
    kubectl apply -f kube_configs/dist.yml
    echo "waiting for dist copy ..."; sleep 15
    kubectl delete -f kube_configs/dist.yml
    echo "done. ingress may need ~5min to boot."
}

main
