FROM docker.openmodelica.org/build-deps:v1.16.2

RUN apt-get update \
  && apt-get install -qy gnupg wget ca-certificates apt-transport-https sudo \
  && echo "deb https://build.openmodelica.org/omc/builds/linux/releases/1.14.2/ `lsb_release -sc`  release" > /etc/apt/sources.list.d/openmodelica.list \
  && wget https://build.openmodelica.org/apt/openmodelica.asc -O- | apt-key add - \
  && apt-get update \
  && apt-get install -qy --no-install-recommends omc \
  && rm -rf /var/lib/apt/lists/*
RUN pip2 install --no-cache pytest psutil
