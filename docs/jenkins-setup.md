# Jenkins Setup & Integration Guide

## 1. Prerequisites
- Jenkins 2.440+ LTS
- Docker Pipeline Plugin
- Warnings NG Plugin
- Configuration as Code (CasC) Plugin

## 2. Docker Compose Local Test Controller
To start a local test Jenkins controller:
```bash
docker compose up -d jenkins
```
The instance will load `jenkins/casc.yaml` and configure a pre-provisioned multibranch pipeline.

## 3. Pipeline Configuration
Add `Jenkinsfile` from this repository to your branch source. The pipeline will automatically discover environment variables and execute all 15 stages.
