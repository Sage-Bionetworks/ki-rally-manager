[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/sagebionetworks/ki-rally-manager)](https://hub.docker.com/r/sagebionetworks/ki-rally-manager/)


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
rallymanager -c CONFIG.json create-sprint rally_number sprint_letter
```

## Get a list of rallies

```
rallymanager -c CONFIG.json get-rallies
```

## Get a list of sprints

```
rallymanager -c CONFIG.json get-rallies [rally_number]
```

## Docker

Mount a [Synapse configuration file](https://docs.synapse.org/articles/client_configuration.html) to `/synapseConfig` and use the provided rally configuration file.

```
docker run -v /home/kdaily/.synapseConfig:/synapseConfig sagebionetworks/ki-rally-manager:latest rallymanager --config /ki-rallies-config.json --synapseConfig /synapseConfig -h
```
