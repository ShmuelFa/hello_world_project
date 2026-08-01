# Hello World — DevOps CI/CD Pipeline

## Project Overview

This project demonstrates a complete DevOps pipeline that automatically **builds, tests, scans, packages, and deploys** a containerized "Hello World" web application to Kubernetes, following GitOps-friendly practices.

**Flow:**

```
GitHub (source) → Jenkins (CI/CD) → Docker Hub (registry) → Kubernetes (runtime)
```

- **Application:** A minimal Flask web app serving a "Hello World" page and a `/health` endpoint.
- **CI/CD:** Jenkins pipeline defined as code (`Jenkinsfile`) — clone, build/test, containerize, scan, push, deploy.
- **Container Registry:** Docker Hub.
- **Orchestration:** Kubernetes (standard k8s cluster via `kubeadm`), using a Deployment (2+ replicas, resource limits) and a NodePort Service.

### Repository Structure

```
.
├── app/
│   ├── app.py            # Flask application
│   ├── test_app.py       # Unit tests
│   └── requirements.txt  # Python dependencies
├── Dockerfile
├── Jenkinsfile
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
```

---

## Prerequisites

Install the following on your build/deploy machine (or VM):

| Tool | Purpose | Install Reference |
|------|---------|--------------------|
| **Docker** | Build & run container images | https://docs.docker.com/engine/install/ |
| **Jenkins** | CI/CD automation server (install on a VM or as a container) | https://www.jenkins.io/doc/book/installing/ |
| **Kubernetes (k8s)** | Container orchestration cluster for deployment (via `kubeadm`, or any conformant cluster) | https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/ |
| **git** | Version control | https://git-scm.com/downloads |

Also required:
- A **Docker Hub** account (for pushing images).
- `kubectl` configured (via kubeconfig) to talk to your cluster.
- Jenkins plugins: `Docker Pipeline`, `Git`, `Kubernetes CLI` (or just `kubectl` on PATH).
- Jenkins credentials configured:
  - `dockerhub-credentials` → Username/Password credential for Docker Hub.
  - `kubeconfig-credentials` → Secret file credential containing your cluster's kubeconfig.

---

## Deployment Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

### 2. Set up a Kubernetes cluster (example, single control-plane node via kubeadm)
```bash
# Install a container runtime (containerd) first, then:
sudo apt-get update && sudo apt-get install -y kubelet kubeadm kubectl
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Configure kubectl for your user
mkdir -p ~/.kube
sudo cp -i /etc/kubernetes/admin.conf ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Install a pod network add-on (example: Flannel)
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# Single-node clusters only: allow scheduling on the control-plane node
kubectl taint nodes --all node-role.kubernetes.io/control-plane-

kubectl get nodes
```
> Alternative: if you just need a quick local cluster instead of a full `kubeadm` setup, `minikube start` or Docker Desktop's built-in Kubernetes also work with the manifests in this repo unchanged.

### 3. Run Jenkins (example, as a container)
```bash
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```
Unlock Jenkins, install suggested plugins, then add the credentials listed in **Prerequisites**.

### 4. Create the Jenkins Pipeline job
- New Item → Pipeline → point "Pipeline script from SCM" to this repository, script path `Jenkinsfile`.
- Update the `DOCKERHUB_USER` and `GIT_REPO` variables at the top of the `Jenkinsfile` to match your own account/repo.

### 5. Run the pipeline
Trigger a build manually or via a GitHub webhook. The pipeline will:
1. Clone the repo
2. Install dependencies & run unit tests
3. Build the Docker image (`docker build -t <dockerhub-user>/hello-world:v<build#> .`)
4. Scan the image for HIGH/CRITICAL vulnerabilities (Trivy)
5. Push the image to Docker Hub
6. Apply the Kubernetes manifests and roll out the new image

### 6. Verify the deployment
```bash
kubectl get pods -l app=hello-world
kubectl get svc hello-world-service
```
Open the app in a browser:
```
http://<node-ip>:30080
```

### 7. Manual build/push/deploy (without Jenkins, for testing)
```bash
docker build -t <dockerhub-user>/hello-world:v1 .
docker push <dockerhub-user>/hello-world:v1

kubectl apply -f k8s/deployment.yaml   # after replacing IMAGE_PLACEHOLDER
kubectl apply -f k8s/service.yaml
```

---

## Jenkins Pipeline Screenshots

> Add screenshots here after running the pipeline in your own Jenkins instance:
>
> 1. **Pipeline overview** — stage view showing all green stages (Clone → Build → Docker Build → Scan → Push → Deploy).
> 2. **Console output** — successful `docker push` and `kubectl rollout status` output.
> 3. **Docker Hub** — the pushed image tag visible in your repository.
>
> Example placeholders:
> `docs/screenshots/pipeline-success.png`
> `docs/screenshots/console-output.png`
> `docs/screenshots/dockerhub-image.png`

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| `docker: permission denied` in Jenkins | Jenkins user can't access Docker socket | Add `jenkins` user to the `docker` group, or mount `/var/run/docker.sock` if Jenkins runs in a container; restart Jenkins |
| `ImagePullBackOff` in `kubectl get pods` | Image name/tag wrong, or image is private | Verify `IMAGE_PLACEHOLDER` was correctly substituted; confirm the image exists on Docker Hub and is public (or add an `imagePullSecret`) |
| Jenkins can't reach cluster (`kubectl` errors) | Missing/invalid kubeconfig credential | Re-check the `kubeconfig-credentials` secret file content and that the API server is reachable from the Jenkins host |
| `docker login` fails in pipeline | Wrong/expired Docker Hub credentials | Recreate the `dockerhub-credentials` entry in Jenkins with a valid Docker Hub access token |
| Pods stuck in `Pending` | Insufficient cluster resources | Lower `resources.requests` in `deployment.yaml`, or check `kubectl describe pod <pod>` for scheduling errors |
| App not reachable at `http://<node-ip>:30080` | Firewall blocking NodePort, or wrong node IP | Confirm the NodePort range (30000-32767) is open; use `kubectl get nodes -o wide` for the correct IP |
| `pytest`/`unittest` step fails in Jenkins | Missing Python or dependency issue | Ensure the Jenkins agent has Python 3.12 available, or run the build stage inside a Docker agent |
| Trivy stage fails the whole build | Scan configured to fail on findings | This pipeline uses `--exit-code 0` (report only); change to `--exit-code 1` if you want vulnerabilities to fail the build |

---

## Notes

- Update `DOCKERHUB_USER` and `GIT_REPO` in `Jenkinsfile` before running.
- The Kubernetes Service uses `NodePort` for simplicity; switch `type: LoadBalancer` if your cluster/cloud provider supports it.
- Image tags use the Jenkins `BUILD_NUMBER` (e.g., `v12`) so every pipeline run produces a unique, traceable image.
