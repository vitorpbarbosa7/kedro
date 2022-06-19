FROM python:3.8

WORKDIR /code

COPY requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt

COPY kedro_api/ kedro_api/

# command to run on start:

WORKDIR /code/kedro_api

ENTRYPOINT ["/bin/bash","entrypoint.sh"]

