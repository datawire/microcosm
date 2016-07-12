FROM alpine:3.4
MAINTAINER Philip Lombardi <plombardi@datawire.io>
EXPOSE 5000
LABEL DESCRIPTION="Datawire Microcosm Service"
LABEL LICENSE="Apache 2.0"
LABEL VENDOR="Datawire"

RUN apk add --update \
    bash \
    curl \
    python \
    python-dev \
    py-pip \
    build-base \
    && pip install virtualenv virtualenvwrapper \
    && rm -rf /var/cache/apk/*

WORKDIR /service
COPY . /service
RUN virtualenv /venv && /venv/bin/pip install -r /service/requirements.txt
RUN . /venv/bin/activate; curl -sL https://raw.githubusercontent.com/datawire/mdk/master/install.sh | bash -s --

CMD ["/venv/bin/python", "microsym", "service.yml"]
