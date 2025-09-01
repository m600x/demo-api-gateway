# Demo - API Gateway for an LLM

## Description
This is a very basic python app that serve as an api gateway for LLM query.
- `POST` on `/completion`, forwarded to ollama or send an altered prompt
- `GET` on `/logs` to dump logs

Built using Flask, it support the following:
- Two logger: stdout, file
- Get or generate a *x-request-id* to track the lifecycle of a request
- Calculate the latency of response
- Handle the most obvious error: file access, malformed request, etc...

As for the Ops side (primary used Gitlab CI but since Github Actions seems to be the tool used here, I've adapted):
- Kubernetes artifacts and Helm chart
- CI: Test the app (pytest dummy)
- CI: Build and push to docker hub

## Usage

Choose your prefered method (local, docker, kubernetes) following the instructions below and head to `http://localhost:8080`.

Since it's a proof of concept, no public LoadBalancer is set, only Cluster IP and a port-forward from K8s to access it.

### Pre-requirement
The demo work without ollama but it's designed to forward the request to an LLM. So to launch a local ollama instance and pull llama2, use:
```
docker-compose up -d
docker exec ollama ollama pull llama2
```

Once that done, export the URL:
```
export OLLAMA_URL=http://localhost:11434/api/generate
```
Note that on mac it's `http://docker.for.mac.localhost:11434/api/generate`.

With or without the env variable, the demo should still "work" as it will detect an empty value or even if the URL is invalid, catch the error and fallback to the default behavior (altered prompt)

### Local execution
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 -m flask --app app run --host=0.0.0.0 --port=8080
```

### Docker execution
Using the public container:
```
docker run -it --rm -p 8080:8080 -v ./logs:/logs -e OLLAMA_URL=$OLLAMA_URL m600x/demo-api-gateway:latest
```

Alternatively, if you want to run a local version:
```
docker build -t demo .
docker run -it --rm -p 8080:8080 -v ./logs:/logs -e OLLAMA_URL=$OLLAMA_URL demo
```
### Kubernetes execution

#### Using YAML files
```
kubectl apply -f kubernetes/
kubectl port-forward svc/demo-api-gateway 8080:8080
```

If you have ollama running locally, execute:
```
kubectl set env deploy/demo-api-gateway OLLAMA_URL=http://host.minikube.internal:11434
```

#### Using Helm chart
```
helm install demo demo-api-gateway
kubectl port-forward svc/demo-demo-api-gateway 8080:8080
```
