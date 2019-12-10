_ = {
    "kind": "PodMetricsList",
    "apiVersion": "metrics.k8s.io/v1beta1",
    "metadata": {"selfLink": "/apis/metrics.k8s.io/v1beta1/pods"},
    "items": [
        {
            "metadata": {
                "name": "foiled-salamander-nfs-server-provisioner-0",
                "namespace": "default",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods/foiled-salamander-nfs-server-provisioner-0",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:39Z",
            "window": "30s",
            "containers": [
                {
                    "name": "nfs-server-provisioner",
                    "usage": {"cpu": "2876511n", "memory": "14970944Ki"},
                }
            ],
        },
        {
            "metadata": {
                "name": "kube-dns-79868f54c5-h5rts",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-79868f54c5-h5rts",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:40Z",
            "window": "30s",
            "containers": [
                {"name": "prometheus-to-sd", "usage": {"cpu": "0", "memory": "9800Ki"}},
                {"name": "sidecar", "usage": {"cpu": "655158n", "memory": "14104Ki"}},
                {"name": "kubedns", "usage": {"cpu": "1242843n", "memory": "11504Ki"}},
                {"name": "dnsmasq", "usage": {"cpu": "203919n", "memory": "7504Ki"}},
            ],
        },
        {
            "metadata": {
                "name": "server-deployment-69555ddc6f-q8cfk",
                "namespace": "default",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods/server-deployment-69555ddc6f-q8cfk",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:48Z",
            "window": "30s",
            "containers": [
                {"name": "django", "usage": {"cpu": "7642513n", "memory": "100864Ki"}},
                {"name": "nginx", "usage": {"cpu": "335047n", "memory": "2764Ki"}},
            ],
        },
        {
            "metadata": {
                "name": "tiller-deploy-695779d66-mmxck",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/tiller-deploy-695779d66-mmxck",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:54Z",
            "window": "30s",
            "containers": [
                {"name": "tiller", "usage": {"cpu": "114097n", "memory": "8748Ki"}}
            ],
        },
        {
            "metadata": {
                "name": "heapster-679bdb88fd-7ggnh",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/heapster-679bdb88fd-7ggnh",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:43Z",
            "window": "30s",
            "containers": [
                {
                    "name": "heapster-nanny",
                    "usage": {"cpu": "288049n", "memory": "10640Ki"},
                },
                {"name": "heapster", "usage": {"cpu": "260513n", "memory": "27300Ki"}},
                {"name": "prom-to-sd", "usage": {"cpu": "12386n", "memory": "12460Ki"}},
            ],
        },
        {
            "metadata": {
                "name": "fluentd-gcp-scaler-59b7b75cd7-2jtkz",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/fluentd-gcp-scaler-59b7b75cd7-2jtkz",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:46Z",
            "window": "30s",
            "containers": [
                {
                    "name": "fluentd-gcp-scaler",
                    "usage": {"cpu": "19793304n", "memory": "44932Ki"},
                }
            ],
        },
        {
            "metadata": {
                "name": "prometheus-to-sd-wjzxc",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/prometheus-to-sd-wjzxc",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:45Z",
            "window": "30s",
            "containers": [
                {
                    "name": "prometheus-to-sd",
                    "usage": {"cpu": "1136643n", "memory": "10208Ki"},
                },
                {
                    "name": "prometheus-to-sd-new-model",
                    "usage": {"cpu": "1666412n", "memory": "10372Ki"},
                },
            ],
        },
        {
            "metadata": {
                "name": "kube-dns-79868f54c5-nd98r",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-79868f54c5-nd98r",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:44Z",
            "window": "30s",
            "containers": [
                {
                    "name": "prometheus-to-sd",
                    "usage": {"cpu": "8905n", "memory": "9436Ki"},
                },
                {"name": "sidecar", "usage": {"cpu": "805788n", "memory": "14076Ki"}},
                {"name": "dnsmasq", "usage": {"cpu": "141596n", "memory": "7500Ki"}},
                {"name": "kubedns", "usage": {"cpu": "1164140n", "memory": "11132Ki"}},
            ],
        },
        {
            "metadata": {
                "name": "kube-proxy-gke-standard-cluster-1-default-pool-4104a659-gzk5",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-proxy-gke-standard-cluster-1-default-pool-4104a659-gzk5",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:42Z",
            "window": "30s",
            "containers": [
                {
                    "name": "kube-proxy",
                    "usage": {"cpu": "2569792n", "memory": "25196Ki"},
                }
            ],
        },
        {
            "metadata": {
                "name": "l7-default-backend-fd59995cd-fb4qd",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/l7-default-backend-fd59995cd-fb4qd",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:48Z",
            "window": "30s",
            "containers": [
                {
                    "name": "default-http-backend",
                    "usage": {"cpu": "111616n", "memory": "4928Ki"},
                }
            ],
        },
        {
            "metadata": {
                "name": "event-exporter-v0.2.4-5f88c66fb7-gglmh",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/event-exporter-v0.2.4-5f88c66fb7-gglmh",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:43Z",
            "window": "30s",
            "containers": [
                {
                    "name": "prometheus-to-sd-exporter",
                    "usage": {"cpu": "0", "memory": "11640Ki"},
                },
                {"name": "event-exporter", "usage": {"cpu": "0", "memory": "20136Ki"}},
            ],
        },
        {
            "metadata": {
                "name": "prometheus-to-sd-l79vn",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/prometheus-to-sd-l79vn",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:39Z",
            "window": "30s",
            "containers": [
                {
                    "name": "prometheus-to-sd",
                    "usage": {"cpu": "25934n", "memory": "11188Ki"},
                },
                {
                    "name": "prometheus-to-sd-new-model",
                    "usage": {"cpu": "10611n", "memory": "11024Ki"},
                },
            ],
        },
        {
            "metadata": {
                "name": "kube-dns-autoscaler-bb58c6784-pl48z",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-autoscaler-bb58c6784-pl48z",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:41Z",
            "window": "30s",
            "containers": [
                {"name": "autoscaler", "usage": {"cpu": "332198n", "memory": "13516Ki"}}
            ],
        },
        {
            "metadata": {
                "name": "fluentd-gcp-v3.2.0-5bvqm",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/fluentd-gcp-v3.2.0-5bvqm",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:43Z",
            "window": "30s",
            "containers": [
                {
                    "name": "fluentd-gcp",
                    "usage": {"cpu": "16647458n", "memory": "325136Ki"},
                },
                {
                    "name": "prometheus-to-sd-exporter",
                    "usage": {"cpu": "18957n", "memory": "9632Ki"},
                },
            ],
        },
        {
            "metadata": {
                "name": "kube-proxy-gke-standard-cluster-1-default-pool-4104a659-zj24",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-proxy-gke-standard-cluster-1-default-pool-4104a659-zj24",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:40Z",
            "window": "30s",
            "containers": [
                {
                    "name": "kube-proxy",
                    "usage": {"cpu": "2367211n", "memory": "24684Ki"},
                }
            ],
        },
        {
            "metadata": {
                "name": "metrics-server-v0.3.1-57c75779f-gnpf7",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/metrics-server-v0.3.1-57c75779f-gnpf7",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:52Z",
            "window": "30s",
            "containers": [
                {
                    "name": "metrics-server-nanny",
                    "usage": {"cpu": "175313n", "memory": "12252Ki"},
                },
                {
                    "name": "metrics-server",
                    "usage": {"cpu": "868039n", "memory": "28248Ki"},
                },
            ],
        },
        {
            "metadata": {
                "name": "fluentd-gcp-v3.2.0-qn57s",
                "namespace": "kube-system",
                "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/fluentd-gcp-v3.2.0-qn57s",
                "creationTimestamp": "2019-12-10T16:47:13Z",
            },
            "timestamp": "2019-12-10T16:46:53Z",
            "window": "30s",
            "containers": [
                {
                    "name": "prometheus-to-sd-exporter",
                    "usage": {"cpu": "15180n", "memory": "11872Ki"},
                },
                {
                    "name": "fluentd-gcp",
                    "usage": {"cpu": "21200453n", "memory": "348300Ki"},
                },
            ],
        },
    ],
}

