# Podman sample & cheatsheet

### Podman commands

```bash
podman info      # prints config; errors here usually mean subuid/networking issues
podman run --rm quay.io/podman/hello
podman pod ps [-a]
podman ps [-a] [--pod]
podman image ls
podman network ls
podman volume ls

podman pod create --name hello-pod -p 8080:80
podman run -d --pod hello-pod --name web docker.io/library/nginx:alpine
podman run --rm --pod hello-pod docker.io/curlimages/curl -s localhost:80
podman kube generate hello-pod > hello.yaml      # save it as YAML

podman pod stop hello-pod
podman pod rm [-f] hello-pod   # remove the pod and everything in it
```

### Podman kube - compose like

```bash
podman kube play --build hello.yaml          # like: compose up --build
curl localhost:8080
podman pod ps                                # the "hello" pod and its containers
podman logs hello-web                        # containers are named <pod>-<container>
podman kube play --replace --build hello.yaml  # after editing code: rebuild + recreate
podman kube down hello.yaml                  # like: compose down

# Deploy to k8s cluster
podman kube apply --kubeconfig ~/.kube/config -f hello.yaml   # send the YAML to the cluster
podman kube apply --kubeconfig ~/.kube/config hello            # or send a running pod directly
```

### Podman quadlet - run using systemd and for background

```bash
podman build -t hello-app ./hello-app   # the .kube file runs images, it doesn't build them
podman kube down hello.yaml             # stop the copy you started by hand, if it's running
podman quadlet install hello.kube
podman quadlet list                   # see installed quadlets
systemctl --user daemon-reload
systemctl --user start hello.service
curl localhost:8080

# Check
systemctl --user status hello.service
journalctl --user -u hello.service

systemctl --user stop hello.service   # stop: removes the pod and its containers
podman quadlet rm hello.kube          # remove: deletes the installed .kube file
systemctl --user daemon-reload        # tell systemd the service is gone
```
