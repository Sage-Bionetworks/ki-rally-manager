[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/sagebionetworks/ki-rally-manager)](https://hub.docker.com/r/sagebionetworks/ki-rally-manager/)


# ki Rally Manager

Project management code for ki rallies and sprints.

# Install

```
pip install git+https://github.com/Sage-Bionetworks/ki-rally-manager.git
```
# Usage

Use requires a configuration file in `json` format that contains information where things will be set up. An example is at [`test-config.json`](test-config.json).

For ki rallies, use the [`ki-rallies-config.json`](ki-rallies-config.json). Appropriate permissions in Synapse are required to use this configuration.

The manager is generally used via the provided command line interface. To get help and see the available features:

```
rallymanager -h
```

## Create a sprint (and a rally)

This creates a rally project, rally team(s), and adds the rally project to the rally project index. If you do not want to use your cached Synapse credentials, you may include a `--synapse_config` argument with the path to a Synapse configuration file.

```
rallymanager --config CONFIG.json --synapse_config ~/.synapseConfig create-rally rally_number
```

Create a sprint project with folder hierarchy, add wiki content, and post discussion forum posts.

```
rallymanager --config CONFIG.json --synapse_config ~/.synapseConfig create-sprint rally_number sprint_letter
```

See `rallymanager create-rally -h` and `rallymanager create-sprint -h` for more parameters.

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
