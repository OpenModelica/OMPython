FROM docker.openmodelica.org/build-deps

RUN apt-get update \
  && apt-get install -qy gnupg wget ca-certificates apt-transport-https sudo \
  && echo "deb https://build.openmodelica.org/apt `lsb_release -sc`  release" > /etc/apt/sources.list.d/openmodelica.list \
  && wget https://build.openmodelica.org/apt/openmodelica.asc -O- | apt-key add - \
  && apt-get update \
  && apt-get install -qy --no-install-recommends omc \
  && pip2 install pytest \
  && pip3 install pytest \
  && rm -rf /var/lib/apt/lists/*
