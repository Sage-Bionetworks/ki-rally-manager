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
bootstrap-rally-sprint RALLYNUMBER SPRINTLETTER
```

## Get a list of rallies

```
bootstrap-rally-sprint get-rallies
```

## Get a list of sprints

```
bootstrap-rally-sprint get-rallies [RALLYNUMBER]
```

