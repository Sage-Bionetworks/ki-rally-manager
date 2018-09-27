[![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?style=flat-square)](https://hub.docker.com/r/dailyk/hbgdki-bootstrap/)

# hbgdki-bootstrap

Project management code for HBGDki rallies and sprints.

# Install

```
pip install git+https://github.com/Sage-Bionetworks/hbgdki-bootstrap.git
```
# Usage

## Create a sprint (and a rally)

```
rally-manger -c CONFIG.json create-sprint RALLYNUMBER SPRINTLETTER
```

## Get a list of rallies

```
rally-manger -c CONFIG.json get-rallies
```

## Get a list of sprints

```
rally-manger -c CONFIG.json get-rallies [RALLYNUMBER]
```

