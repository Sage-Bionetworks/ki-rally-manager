[![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?style=flat-square)](https://hub.docker.com/r/SageBionetworks/ki-rally-manager/)

# ki Rally Manager

Project management code for ki rallies and sprints.

# Install

```
pip install git+https://github.com/Sage-Bionetworks/ki-rally-manager.git
```
# Usage

Requires a configuration file in `json` format that contains information where things will be set up. An example is at [`ki-rallies-config.json`](ki-rallies-config.json).

## Create a sprint (and a rally)

This creates a rally project, a rally team, and a sprint project. It adds them to the administrative project for listing.

```
rallymanager -c CONFIG.json create-sprint RALLYNUMBER SPRINTLETTER
```

## Get a list of rallies

```
rallymanager -c CONFIG.json get-rallies
```

## Get a list of sprints

```
rallymanager -c CONFIG.json get-rallies [RALLYNUMBER]
```

