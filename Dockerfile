FROM python:3.6

COPY ki-rallies-config.json /ki-rallies-config.json

RUN pip install git+https://github.com/Sage-Bionetworks/ki-rally-manager.git
