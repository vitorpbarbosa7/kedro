FROM python:3.8

WORKDIR /code

COPY ames_package/ ames_package/

WORKDIR /code/ames_package

RUN python3 -m pip install .

WORKDIR /usr/local/lib/python3.8/site-packages/package_ames/

COPY entrypoint.sh .

ENTRYPOINT ["/bin/bash","entrypoint.sh"]
#ENTRYPOINT ["/bin/bash"]
