
[![Github Badge](https://github.com/BennyE/omniportal/actions/workflows/build.yml/badge.svg)](https://github.com/BennyE/omniportal)
[![Github Badge](https://github.com/BennyE/omniportal/actions/workflows/development.yml/badge.svg?branch=dev)](https://github.com/BennyE/omniportal)
[![Badge](https://img.shields.io/badge/amd64-Available%20on%20Quay%2Eio-30c452.svg)](https://quay.io/bennye_hh/omniportal)
[![Badge](https://img.shields.io/badge/arm-Available%20on%20Quay%2Eio-30c452.svg)](https://quay.io/bennye_hh/omniportal)
[![Badge](https://img.shields.io/badge/arm64-Available%20on%20Quay%2Eio-30c452.svg)](https://quay.io/bennye_hh/omniportal)

# OmniPortal

OmniPortal - a Flask-based portal that intends to simply the creation of Guests &amp; Employees in Alcatel-Lucent Enterprise OmniVista.
The idea is that OmniPortal can be hosted on Alcatel-Lucent Enterprise OmniSwitch with AOS Release 8 in the future.

## Run OmniPortal

You have multiple options to run OmniPortal
- I recommend to regularly take a backup of your ~/conf/ directory at a secure place

### Run OmniPortal (locally on your machine)

There are a couple of additional things that need to be done for the OmniSwitch, e.g. updating the paths to /flash/python/
This is work-in-progress, so expect rough edges! **I strongly recommend to work with a .venv!**

`git clone https://github.com/BennyE/omniportal.git`

`python3 -m pip install -r requirements.txt`

`python3 -m flask --app omniportal --debug run --host 0.0.0.0 --port 5000`

- ~~You'll want to update your **app.secret_key** before you do anything else~~ (all automated in current build)
- Navigate to 127.0.0.1:5000 (you don't want to run **debug** if outside of development phase)
- Attempt to login with admin/admin123, the attempt will fail and inform you that "admin/"`<Take note of your random password!>` account was created in **omniportal_users.json** 
- Navigate to /admin and do your settings
- Change your password! ~~Please don't use something valuable, as the **omniportal_users.json** stores this unencrypted (as of now)!~~ **DONE >= v0.0.6** 

### Run OmniPortal in Docker (local build)

You'll find the files that store the configuration/settings in **/home/$USER/omniportal_conf/**

#### Build locally

`sudo docker build --tag omniportal:latest .`

#### Run OmniPortal

`sudo docker run --rm --name omniportal -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d omniportal:latest`

#### Optional: Run OmniPortal with --debug

`sudo docker run --rm --name omniportal -e EXTRA_OPTIONS="--debug" -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d omniportal:latest`

#### Stop OmniPortal-Docker

`sudo docker stop omniportal`

### Run OmniPortal (my image) from Quay.io

You'll find the files that store the configuration/settings in **/home/$USER/omniportal_conf/**

`sudo docker run --rm --name omniportal -v ~/omniportal_conf/:/usr/src/app/conf/ -p 5000:5000 -d quay.io/bennye_hh/omniportal:latest`

#### Stop OmniPortal-Docker

`sudo docker stop omniportal`

### Run OmniPortal in Rancher Desktop / k3s / k8s

You are able to run OmniPortal on your favorite flavour of kubernetes. The following outputs are taken from my Rancher Desktop on Apple MBP with Apple Silicon.
The container images are available for `amd64`, `arm` & `arm64` from: ![quay.io/bennye_hh/omniportal](https://quay.io/bennye_hh/omniportal)

#### kubectl get nodes

```
benny@Bennys-MacBook-Pro ~ % kubectl get nodes
NAME                   STATUS   ROLES                  AGE   VERSION
lima-rancher-desktop   Ready    control-plane,master   66m   v1.24.6+k3s1
```

#### kubectl get pods -A

```
benny@Bennys-MacBook-Pro ~ % kubectl get pods -A
NAMESPACE     NAME                                      READY   STATUS      RESTARTS   AGE
kube-system   svclb-traefik-748d5f86-hbw84              2/2     Running     0          66m
kube-system   helm-install-traefik-crd-877ks            0/1     Completed   0          66m
kube-system   helm-install-traefik-xg99r                0/1     Completed   0          66m
kube-system   coredns-b96499967-msv6t                   1/1     Running     0          66m
kube-system   traefik-7cd4fcff68-lbsjg                  1/1     Running     0          66m
kube-system   metrics-server-668d979685-26zrm           1/1     Running     0          66m
kube-system   local-path-provisioner-7b7dc8d6f5-dwjbb   1/1     Running     0          66m
```

#### kubectl get sc

```
benny@Bennys-MacBook-Pro ~ % kubectl get sc
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  66m
```

#### Change directory to OmniPortal deploy directory

Change directory to where you cloned/downloaded the OmniPortal deploy `.yaml` files. 
```
benny@Bennys-MacBook-Pro ~ % cd python/omniportal/deploy
```

#### Review/Update ingress-omniportal.yaml 

Adapt `ingress-omniportal.yaml` to your needs. If you run Rancher Desktop, you can access the OmniPortal at `http(s)://omniportal.127.0.0.1.sslip.io`.
Note that the HTTPS/TLS certificate is the default certificate coming with Traefik and will throw an error message in your browser.

```
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.class: traefik
  name: ingress-omniportal
spec:
  rules:
  - host: omniportal.127.0.0.1.sslip.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: omniportal
            port:
              number: 5000

```

#### kubectl apply --dry-run=client -o yaml -k . --validate=true

After you adapted the configuration to your needs, validate before deployment.

```
benny@Bennys-MacBook-Pro deploy % kubectl apply --dry-run=client -o yaml -k . --validate=true
apiVersion: v1
items:
- apiVersion: v1
  kind: Namespace
  metadata:
    annotations:
      kubectl.kubernetes.io/last-applied-configuration: |
        {"apiVersion":"v1","kind":"Namespace","metadata":{"annotations":{},"name":"omniportal"},"spec":{}}
    creationTimestamp: "2022-10-22T12:08:34Z"
    labels:
      kubernetes.io/metadata.name: omniportal
    name: omniportal
# ... a lot more output    
```

#### kubectl apply -k . 

Assuming that everything went fine, we deploy OmniPortal now.
```
benny@Bennys-MacBook-Pro deploy % kubectl apply -k .                                         
namespace/omniportal created
service/omniportal created
persistentvolumeclaim/omniportal created
deployment.apps/omniportal created
ingress.networking.k8s.io/ingress-omniportal created
```

### What if OmniPortal doesn't work in Rancher Desktop (or k3s/k8s)?

#### Readiness probe failed

Synopsis: OmniPortal not available

Reason: Readiness probe failed

Solution: Fixed in >= v0.0.2

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get pods
NAME                          READY   STATUS    RESTARTS   AGE
omniportal-69d887b7b7-rzb6g   0/1     Running   0          26s
```

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get events
LAST SEEN   TYPE      REASON                  OBJECT                             MESSAGE
67s         Normal    WaitForFirstConsumer    persistentvolumeclaim/omniportal   waiting for first consumer to be created before binding
67s         Normal    ScalingReplicaSet       deployment/omniportal              Scaled up replica set omniportal-69d887b7b7 to 1
67s         Normal    SuccessfulCreate        replicaset/omniportal-69d887b7b7   Created pod: omniportal-69d887b7b7-rzb6g
67s         Normal    ExternalProvisioning    persistentvolumeclaim/omniportal   waiting for a volume to be created, either by external provisioner "rancher.io/local-path" or manually created by system administrator
67s         Normal    Provisioning            persistentvolumeclaim/omniportal   External provisioner is provisioning volume for claim "omniportal/omniportal"
64s         Normal    ProvisioningSucceeded   persistentvolumeclaim/omniportal   Successfully provisioned volume pvc-dabe3ec3-61e8-4266-96c6-793c1ce04112
62s         Normal    Scheduled               pod/omniportal-69d887b7b7-rzb6g    Successfully assigned omniportal/omniportal-69d887b7b7-rzb6g to lima-rancher-desktop
62s         Normal    Pulling                 pod/omniportal-69d887b7b7-rzb6g    Pulling image "quay.io/bennye_hh/omniportal:latest"
53s         Normal    Pulled                  pod/omniportal-69d887b7b7-rzb6g    Successfully pulled image "quay.io/bennye_hh/omniportal:latest" in 9.649704921s
53s         Normal    Created                 pod/omniportal-69d887b7b7-rzb6g    Created container omniportal
53s         Normal    Started                 pod/omniportal-69d887b7b7-rzb6g    Started container omniportal
2s          Warning   Unhealthy               pod/omniportal-69d887b7b7-rzb6g    Readiness probe failed: HTTP probe failed with statuscode: 404
```

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal exec -it omniportal-69d887b7b7-rzb6g -- bash
root@omniportal-69d887b7b7-rzb6g:/usr/src/app# 
```

(In the meantime I fixed the path for the readiness probe in `deployment-omniportal.yaml`)

```
benny@Bennys-MacBook-Pro deploy % kubectl apply -k .                                                
namespace/omniportal unchanged
service/omniportal unchanged
persistentvolumeclaim/omniportal unchanged
deployment.apps/omniportal configured
ingress.networking.k8s.io/ingress-omniportal unchanged
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get deployment                              
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
omniportal   1/1     1            1           9m37s
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get pods      
NAME                          READY   STATUS        RESTARTS   AGE
omniportal-57f97c5f4f-lsg95   1/1     Running       0          20s
omniportal-69d887b7b7-rzb6g   0/1     Terminating   0          9m46s
```

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal describe node lima-rancher-desktop
Name:               lima-rancher-desktop
Roles:              control-plane,master
```

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get ingress   
NAME                 CLASS    HOSTS                           ADDRESS          PORTS   AGE
ingress-omniportal   <none>   omniportal.127.0.0.1.sslip.io   192.168.11.197   80      4h40m
```

#### Delete/Access configuration from persistent volume (pv) in Rancher Desktop

OmniPortal uses a local-path storage class. In Rancher Desktop this can be found **inside** the `lima-rancher-desktop` VM.

You may need to access this to remove/edit files after changes that are marked as `BREAKING-CHANGE`!

```
benny@Bennys-MacBook-Pro deploy % kubectl get pv    
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                   STORAGECLASS   REASON   AGE
pvc-dabe3ec3-61e8-4266-96c6-793c1ce04112   500Mi      RWO            Delete           Bound    omniportal/omniportal   local-path              4h51m
```

```
benny@Bennys-MacBook-Pro % rdctl shell 
lima-rancher-desktop$ sudo su -
lima-rancher-desktop:~# cd /var/lib/rancher/k3s/storage
lima-rancher-desktop:/var/lib/rancher/k3s/storage# ls
pvc-dabe3ec3-61e8-4266-96c6-793c1ce04112_omniportal_omniportal
lima-rancher-desktop:/var/lib/rancher/k3s/storage# cd pvc-dabe3ec3-61e8-4266-96c6-793c1ce04112_omniportal_omniportal/
lima-rancher-desktop:/var/lib/rancher/k3s/storage/pvc-dabe3ec3-61e8-4266-96c6-793c1ce04112_omniportal_omniportal# ls
omniportal_secret_key.json  omniportal_users.json
```

#### Access logs of the pod

```
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal get pods
NAME                          READY   STATUS    RESTARTS   AGE
omniportal-6f8747c587-bsqkk   1/1     Running   0          159m
benny@Bennys-MacBook-Pro deploy % kubectl -n omniportal logs omniportal-6f8747c587-bsqkk
 * Serving Flask app 'omniportal'
 * Debug mode: off
```

## i18n

Edit the **messages.po** in the **translations/de/LC_MESSAGES** or e.g. **translations/es/LC_MESSAGES**

### Extract (new) translatables into messages.pot

`.venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot .`

### Update the corresponding individual language files

`.venv/bin/pybabel update -i messages.pot -d translations`

### Compile the translation when translation-work is done

`.venv/bin/pybabel compile -d translations`

## TODO & Ideas to be evaluated

1. ~~"Guest" and "Admin"-role are the two only roles taken into account so far~~ **DONE >= v0.0.6** `BREAKING-CHANGE`
2. There is no logic yet that handles "running on OmniSwitch with AOS R8"
3. No Adaptive Card is sent yet after creating the Employee account
4. Avaya OneCloud CPaaS (for e.g. SMS) is not implemented yet
5. The code could need some structuring into multiple files
6. Possibly it would make sense to move to sqlite instead of JSON files, to be evaluated later
7. ~~Create app.secret_key, omniportal_users & omniportal_settings automatically if those don't exist and store in conf directory~~ **DONE >= v0.0.2**
8. ~~Create Dockerfile & distribute via Quay.io~~ **DONE >= v0.0.2** (Thanks to ![dgo19](https://github.com/dgo19) for the help!)
9. ~~Figure out how to setup & deploy OmniPortal to Rancher Desktop (k3s/k8s)~~ **DONE >= v0.0.2** (Thanks to ![dgo19](https://github.com/dgo19) for the help!)
10. ~~Setup fully automated GitHub Actions Workflow for multi-architecture container images~~ **DONE >= v0.0.2** (Thanks to ![dgo19](https://github.com/dgo19) for the help!)
11. ~~Store OmniPortal passwords only as a hash~~ **DONE >= v0.0.6** `BREAKING-CHANGE`
12. Integrate with Grafana/Prometheus
13. ~~Update Dockerfile to do `apt update`, `apt dist-upgrade` & `apt clean` to collect latest updates~~ **DONE >= v0.0.3**
14. ~~Update deployment-omniportal.yaml to a given version e.g. :0.0.3 instead of :latest~~ **DONE >= v0.0.3** 
15. ~~Switch to Python v3.9 Alpine Linux image to make the security scanner of Quay.io happy~~ **DONE >= v0.0.4**
16. Update function for undesireable words in username/password
17. ~~Rework employee module to allow creation of employee-users which are stored with a pseudo-account in cloud~~ **DONE >= v0.0.6**
18. Evaluate an escalation if password modifiction is attempted with wrong token
19. Offer an option to set $TZ in container runtime to address for UTC vs. local time (e.g. CET / Europe/Berlin)
20. Implement email notifications

## Screenshot

![omniportal](https://user-images.githubusercontent.com/5174414/193449734-003135ea-279c-47f2-be88-0051321efc74.png)
