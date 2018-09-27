[![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?style=flat-square)](https://hub.docker.com/r/dailyk/hbgdki-bootstrap/)

# HBGDki Rally Manger

Project management code for HBGDki rallies and sprints.

# Install

```
pip install git+https://github.com/Sage-Bionetworks/hbgdki-bootstrap.git
```
# Usage

Requires a configuration file in `json` format that contains information where things will be set up. An example is at [`ki-rallies-config.json`](ki-rallies-config.json).

## Create a sprint (and a rally)

This creates a rally project, a rally team, and a sprint project. It adds them to the administrative project for listing.

```
rally-manager -c CONFIG.json create-sprint RALLYNUMBER SPRINTLETTER
```

## Get a list of rallies

```
rally-manager -c CONFIG.json get-rallies
```

## Get a list of sprints

```
rally-manager -c CONFIG.json get-rallies [RALLYNUMBER]
```

