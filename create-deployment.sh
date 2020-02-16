#!/bin/sh

# DEFAULTS for all settings:
DOMAIN="bio-no.de"
ZONENAME="us-east1-a"
CLUSTERNAME="bio-node-cluster"
SANAME="bio-node-sa"
# helmversion="v3.0.2"
PROJECTNAME='$fromgcloud'
DBSIZE="10Gi"
# TOTALSTORAGE will be calculated as size per node * nodes
STORAGENODES="3"
VOLUMESIZEPERNODE="1000Gi"
VOLUMEMETASIZEPERNODE="10Gi"
MAXNODES="9"
MACHINETYPE="n1-standard-8"
ACCESSTYPE="-1"
MACHINETYPE="n1-standard-8"

[ -d /usr/local/opt/gettext/bin ] && export PATH="/usr/local/opt/gettext/bin:$PATH"

nontechsettings="ZONENAME CLUSTERNAME PROJECTNAME SANAME DBSIZE VOLUMESIZEPERNODE VOLUMEMETASIZEPERNODE STORAGENODES MAXNODES MACHINETYPE DOMAIN ACCESSTYPE"
allsettings="SETTINGSCONFIRMED DOMAINWAIT $nontechsettings"

confirm() {
    read -e -p "
$1 ${2:-[Y/n]} " YN
    if [ "$YN" = "" ] || [ "$YN" = "y" ] || [ "$YN" = "n" ] || [ "$YN" = "Y" ] || [ "$YN" = "N" ]
    then
        if [ "$YN" = "Y" ]
        then
            YN=y
        fi
        if [ "$YN" = "N" ]
        then
            YN=n
        fi
    else
        confirm "$@"
    fi
}

save_settings() {
    [ -f .bio-node.config ] && rm .bio-node.config
    for setting in $allsettings
    do
        echo "export $setting="\""$(eval 'echo $'$setting)"\" >> .bio-node.config
    done
    source .bio-node.config
}

load_settings() {
    [ -f .bio-node.config ] && source .bio-node.config
    save_settings
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

# helm_subst() {
#     f="$1"
#     shift

#     cat "$f" | envsubst > .helm.yml
#     $helm install "$@" -f .helm.yml
#     rm .helm.yml
# }

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

# install_helm() {
#     mkdir helmdir
#     cd helmdir
#     curl -o helm.tgz --location "https://get.helm.sh/helm-$helmversion-linux-amd64.tar.gz"
#     tar xzf helm.tgz
#     rm helm.tgz
#     cd *
#     mv helm ../../
#     cd ../..
#     rm -rf helmdir
# }

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

confirm_settings() {
    echo "*** Bio-Node Setup ***"
    echo "Please confirm the following settings:"
    
    for setting in $nontechsettings
    do
        echo "$setting: "\""$(eval 'echo $'$setting)"\"
    done
    confirm "Continue?" "[Y/n]"
    if [ "$YN" = "n" ]
    then
        return 1
    fi
}

main() {
    program="$1"
    shift
    requirements || return 1

    if [ "$PROJECTNAME" = '$fromgcloud' ]
    then
        PROJECTNAME="$(gcloud info | grep project | sed -E 's/^.* (.*)$/\1/g' | sed -E 's/(\[|\])//g')"
    fi
    DOMAINWAIT=false
    SETTINGSCONFIRMED=false
    load_settings
    VOLUMESIZEPERNODENUM="$(echo $VOLUMESIZEPERNODE | grep -Eo '\d+')"
    VOLUMESIZEPERNODESUFFIX="$(echo $VOLUMESIZEPERNODE | grep -Eo '[^0-9]+')"
    export TOTALSTORAGE="$((VOLUMESIZEPERNODENUM*STORAGENODES))$VOLUMESIZEPERNODESUFFIX"

    if [ "$ACCESSTYPE" -eq -1 ]
    then
        echo "Select one of the following public access methods:"
        echo " 0: No automatic setup. Create ingress manually later."
        echo " 1: GKE HTTPS Ingress for my domain. ($DOMAIN)"
        read -e -p "
Selected access method: [0] " ACCESSTYPE
        if [ "$ACCESSTYPE" = "" ]
        then
            ACCESSTYPE=0
        fi
    fi

    if ! $SETTINGSCONFIRMED
    then
        confirm_settings || return 1
        SETTINGSCONFIRMED=true
        save_settings
    fi

    if (! $DOMAINWAIT) || (! [ "$ACCESSTYPE" -eq 1 ])
    then
        # if which helm>/dev/null
        # then
        #     helm="helm"
        # else
        #     if ! [ -f helm ]
        #     then
        #         install_helm
        #     fi
        #     helm="./helm"
        # fi
        # helm repo add stable https://kubernetes-charts.storage.googleapis.com/

        rm sa-key.json
        new_account
        sa_secret
        new_cluster

        gcloud container clusters get-credentials $CLUSTERNAME --zone $ZONENAME --project $PROJECTNAME
        if [ "$ACCESSTYPE" -eq 1 ]
        then
            gcloud compute addresses create bio-node-address --global
        fi
    fi
    IPADDRESS="$(gcloud compute addresses list | grep -e '^bio-node-address.*' | grep -oE '\d+.\d+\.\d+\.\d+')"
    echo "Please point $DOMAIN to the following IP address:"
    echo $IPADDRESS
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        DOMAINWAIT=true
        save_settings
        confirm "Domain configured and DNS valid? (check ping)" "[y/N]"
        if ! [ "$YN" = "y" ]
        then
            echo "To continue the process, run"
            echo " $program"
            echo "again."
            return 1
        fi

        DOMAINWAIT=false
    fi
    save_settings

    cd kube_configs
    secretvalues="
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
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        kubectl apply -f cert.yml
    fi
    kubectl apply -f storage/gce.yml
    kubectl apply -f priority.yml
    apply_subst db.yml
    apply_subst cert.yml
    kubectl apply -f storage/rook.yml
    kubectl apply -f storage/rook-operator.yml
    sleep 5
    apply_subst storage/cluster.yml
    sleep 5
    kubectl apply -f storage/fs.yml
    sleep 5
    kubectl apply -f storage/classes.yml
    apply_subst storage/pvc.yml

    echo "waiting for storage to start ..."; sleep 30
    kubectl apply -f $kubeconfigs/deployment.yml
    echo "waiting for server to start ..."; sleep 30
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        kubectl apply -f kube_configs/ingress.yml
    fi
    kubectl apply -f kube_configs/dist.yml
    echo "waiting for dist copy ..."; sleep 15
    kubectl delete -f kube_configs/dist.yml
    echo "done. ingress may need ~5min to boot."
}

main "$0" "$@"
