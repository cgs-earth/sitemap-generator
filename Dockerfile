FROM python:3.9.13-slim

COPY . /build/
WORKDIR /build

RUN \
    # Install dependencies
    apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y git \
    && git clone -b master https://github.com/internetofwater/geoconnex.us.git /geoconnex.us \
    # Install sitemap-generator
    && pip3 install -e . \
    # cleanup
    && apt autoremove -y  \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "sitemap-generator", "run" ]
CMD [ "/build/tests/data/namespaces" ]
