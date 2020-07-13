#!/bin/sh

# DEFAULTS for all settings:
DOMAIN="bio-no.de"
ZONENAME="us-east1-c"
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
NETWORK="default"
SUBNETWORK=""

[ -d /usr/local/opt/gettext/bin ] && export PATH="/usr/local/opt/gettext/bin:$PATH"

nontechsettings="ZONENAME CLUSTERNAME PROJECTNAME SANAME DBSIZE VOLUMESIZEPERNODE VOLUMEMETASIZEPERNODE STORAGENODES MAXNODES MACHINETYPE DOMAIN ACCESSTYPE NETWORK SUBNETWORK"
allsettings="SETTINGSCONFIRMED DOMAINWAIT $nontechsettings"

spin()
{
    spinner='- \ | / - \ | / - \ | / - \ | /'
    for i in $spinner
    do
        printf "$i"
        printf "\010"
        sleep 0.5
    done
}

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
    for r in curl tar gcloud kubectl envsubst jq zip dig
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
    SUBNETWORKPARAM=""
    if [ ! "$SUBNETWORK" = "" ]
    then
        SUBNETWORKPARAM="--subnetwork=$SUBNETWORK"
    fi
    gcloud container clusters create $CLUSTERNAME --image-type ubuntu --machine-type $MACHINETYPE --num-nodes $STORAGENODES --zone $ZONENAME --metadata disable-legacy-endpoints=true --network=$NETWORK $SUBNETWORKPARAM
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
        echo
        echo "Aborting. To change settings:"
        echo " $> vi .bio-node.config"
        return 1
    fi
}

main() {
    program="$1"
    shift
    requirements || return 1

    if ! [ -d kube_configs ]
    then
        echo "Downloading kube_configs..."
        mkdir tmp
        cd tmp
        curl -L -o master.zip https://github.com/bromberglab/bio-node-webserver/archive/master.zip
        unzip master.zip || return 1
        rm master.zip
        cd *
        mv kube_configs ../../
        cd ../../
        rm -rf tmp
    fi

    if [ "$PROJECTNAME" = '$fromgcloud' ]
    then
        PROJECTNAME="$(gcloud info | grep project | sed -E 's/^.* (.*)$/\1/g' | sed -E 's/(\[|\])//g')"
    fi
    DOMAINWAIT=false
    SETTINGSCONFIRMED=false
    load_settings
    gcloud config set project $PROJECTNAME
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

    gcloud auth list 2>/dev/null | grep -E '\*'
    confirm "Use this account for the project?" "[Y/n]"
    [ "$YN" = "n" ] && return 1

    if ! $SETTINGSCONFIRMED
    then
        confirm_settings || return 1
        SETTINGSCONFIRMED=true
        save_settings
    fi

    if (! $DOMAINWAIT)
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

        (cat sa-key.json | grep -o private_key >/dev/null) || rm sa-key.json
        [ -f sa-key.json ] || new_account
        new_cluster
        printf "Waiting for cluster to start ... (up to 4 minutes) "; spin

        while ! gcloud container clusters get-credentials $CLUSTERNAME --zone $ZONENAME --project $PROJECTNAME >/dev/null 2>&1
        do
            spin
        done
        spin
        while ! kubectl get pod >/dev/null 2>&1
        do
            spin
        done
        # wait another 3 minutes to make sure all nodes are there
        for i in $(seq 20)
        do
            spin
        done
        echo
        if [ "$ACCESSTYPE" -eq 1 ]
        then
            gcloud compute addresses create bio-node-address --global
        fi
        sa_secret
    fi
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        IPADDRESS="$(gcloud compute addresses list | grep -e '^bio-node-address.*' | grep -oE '\d+.\d+\.\d+\.\d+')"
        echo "Please point $DOMAIN to the following IP address:"
        echo $IPADDRESS
        DOMAINWAIT=true
        save_settings
        echo "You can stop this process and continue later. Run"
        echo " $program"
        echo "again."
        
        while [ ! "$IPADDRESS" = "$(dig +short "$DOMAIN" | tail -n1)" ]
        do
            printf "Waiting for domain to change... "
            # 80 seconds
            for i in $(seq 10)
            do
                spin
            done
            echo
        done

        DOMAINWAIT=false
    fi
    save_settings

    cd kube_configs
    secretvalues="
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
    if ! grep "sendgrid_key": secret.yml >/dev/null
    then
        confirm "Do you want to use sendgrid to send server mail?" "[y/N]"
        if [ "$YN" = y ]
        then
            SENDGRIDKEY=""
            while [ "$SENDGRIDKEY" = "" ]
            do
                read -e -p "
Sendgrid key: " SENDGRIDKEY
            done
            SENDGRIDSENDER=""
            while [ "$SENDGRIDSENDER" = "" ]
            do
                read -e -p "
Server's sender address (i.e. noreply@bio-no.de): " SENDGRIDSENDER
            done
            grep "sendgrid_key": secret.yml >/dev/null || make_secret "sendgrid_key" "$SENDGRIDKEY"
            grep "sendgrid_sender": secret.yml >/dev/null || make_secret "sendgrid_sender" "$SENDGRIDSENDER"
        fi
    fi

    kubectl apply -f secret.yml
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        apply_subst cert.yml
    fi
    kubectl apply -f storage/gce.yml
    kubectl apply -f priority.yml
    apply_subst db.yml
    kubectl apply -f storage/rook.yml
    kubectl apply -f storage/rook-operator.yml
    sleep 5
    apply_subst storage/cluster.yml
    sleep 5
    kubectl apply -f storage/fs.yml
    sleep 5
    kubectl apply -f storage/classes.yml
    apply_subst storage/pvc.yml

    printf "Waiting for storage to start ... (up to 2 minutes) "
    for i in $(seq 10)
    do
        spin
    done
    echo
    kubectl apply -f deployment.yml
    printf "Waiting for server to start ... (up to 4 minutes) "; spin
    while ! kubectl get pod -l app=server -o json | jq -r '.items[0].status.phase' | grep -i running
    do
        spin
    done
    echo
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        kubectl apply -f ingress.yml
        echo "Ingress may need ~5min to boot."
    fi
    kubectl apply -f dist.yml
    printf "Waiting for dist copy ... "; spin; spin; spin; spin; spin; spin; spin
    echo
    kubectl delete -f dist.yml
    echo "Done."
    echo
    if [ "$ACCESSTYPE" -eq 0 ]
    then
        echo "To access the cluster, run:"
        echo " $> kubectl port-forward service/server-service 8080:80 & sleep 2"
        echo " $> curl localhost:8080/api/.commit/ && echo"
    fi
    if [ "$ACCESSTYPE" -eq 1 ]
    then
        echo "To access the cluster, run:"
        echo " $> curl $DOMAIN/api/.commit/ && echo"
    fi
    echo "To create the admin account, visit $DOMAIN/api/createadmin or localhost:8080/api/createadmin"
}

main "$0" "$@"
