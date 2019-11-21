FROM ubuntu:18.10

RUN apt-get update -y

RUN apt-get install locales -y
RUN locale-gen en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

RUN apt install python3.6 -y
RUN apt install python3-pip -y
RUN apt-get install libspatialindex-dev -y

COPY parcelmap /opt/parcelmap
COPY requirements.txt /opt/requirements.txt

RUN pip3 install -r /opt/requirements.txt
