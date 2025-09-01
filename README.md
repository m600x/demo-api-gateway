# Demo - API Gateway for an LLM

[![ci](https://github.com/m600x/demo-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/m600x/demo-api-gateway/actions/workflows/ci.yml)

## Description
This is a very basic python app that serve as an api gateway for LLM query.

Built using Flask, it support the following:
- `POST` on `/completion`, forwarded to ollama or send an altered prompt
- `GET` on `/logs` to dump logs
- `GET` on `/history` to dump completion logs
- Three logger: stdout, file, history
- Get or generate a *x-request-id* to track the lifecycle of a request
- Calculate the latency of response
- Handle the most obvious error: file access, malformed request, etc...

As for the Ops side (primary used Gitlab CI but since Github Actions seems to be the tool used here, I've adapted):
- Kubernetes artifacts and Helm chart
- CI: Test the app (pytest dummy)
- CI: Test Kubernetes YAML and Helm chart (deploy on kind)
- CI: Scan for vulnerability (only fail on critical with known fix)
- CI: Build and push to docker hub (with SLSA provenance)

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
docker run -it --rm -p 8080:8080 -v ./logs:/logs -e OLLAMA_URL=$OLLAMA_URL m600/demo-api-gateway:latest
```
Note that if you're on Apple Silicon, pull using `docker pull --platform linux/amd64 m600/demo-api-gateway`

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

---

## Notes
Timeframe to do it is four hours (more or less) with my own knowledge. All feature simply couldn't be added without testing since CI/CD part must also be done (and quickly learn Github Actions syntax), no AI "vibe coding" has been used.

I'd rather deliver something simple but tested rather than checking all boxes and not knowning why each line of code exist (*"focus on quality and readability"*).

### Dev improvements
Ain't not backend dev or an expert in Python but with more time allowed, it would have been much better:
- Proper test suite
- an UI with flask templates
- a database to store completion history
- a production WSGI
- Streaming logs and history instead of dumping the whole content
- Monitoring, APM, etc
- Tests, yes I said it twice
- The list goes on and on...

### Ops improvements
- Lint app files
- Dynamic Helm schema for values
- Step to deploy on some internal live cluster
- Report and notification
