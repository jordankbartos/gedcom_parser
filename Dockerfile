FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive

ENV TERM xterm

# Install packages
RUN apt-get update && apt-get -y upgrade

RUN apt-get --assume-yes install \
    dialog \
    apt-utils \
    vim \
    git \
    python3.10 \
    python3.8-venv \
    python3-pip \
    tree

RUN useradd --create-home appuser

USER appuser

RUN mkdir /home/appuser/app
WORKDIR /home/appuser/app

COPY requirements.txt requirements.txt
ENV PATH="${PATH}:/home/appuser/.local/bin"
RUN pip3 install -r requirements.txt
WORKDIR /home/appuser

RUN git clone https://github.com/jordankbartos/my_config.git \
    && cd my_config \
    && sh configure.sh \
    && cd .. \
    && rm -rf my_config

WORKDIR /home/appuser/app/gedcom_parser

#RUN git config user.email --global "jordankbartos@gmail.com" \
#    && git config user.name --global "Jordan Bartos" \
#    && pre-commit install \

CMD ["bash"]
