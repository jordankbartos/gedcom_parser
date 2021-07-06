FROM ubuntu:20.10

ENV TERM xterm

# Install packages
RUN apt-get update \
    && apt-get --assume-yes install dialog \
    apt-utils \
    vim=2:8.2.0716-3ubuntu2 \
    git=1:2.27.0-1ubuntu1.1 \
    python3.8=3.8.10-0ubuntu1~20.10.1 \
    python3-pip=20.1.1-2

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

WORKDIR /home/appuser/app

COPY --chown=appuser . .
RUN pre-commit install \
    && git config user.email "jordankbartos@gmail.com" \
    && git config user.name "Jordan Bartos"

CMD ["bash"]
