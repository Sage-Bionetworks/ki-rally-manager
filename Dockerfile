FROM python:3.7

COPY ki-rallies-config.json /ki-rallies-config.json

COPY . /ki-rally-manager
WORKDIR /ki-rally-manager
RUN pip3 install .
