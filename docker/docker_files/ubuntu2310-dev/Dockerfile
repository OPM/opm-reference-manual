# Stage 1: Build LibreOffice
FROM ubuntu:23.10 as builder
SHELL ["/bin/bash", "-c"]

ARG BUILD_TYPE="release"
ARG GIT_TAG="libreoffice-7.6.5.1"
# Replace default mirror with an alternative mirror
#RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://us.archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.dotsrc.org/ubuntu/|g' /etc/apt/sources.list


# Install necessary packages
# If any packages require configuration of the timezone, they might hang since
# the Docker build process is non-interactive. Avoid this by setting
ENV TZ=Europe/Oslo
# or whatever local timezone, and installing the tzdata package.
RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        build-essential curl g++ git \
        vim sudo wget autoconf libtool \
        cmake tzdata pkg-config \
        zip ccache junit4 libkrb5-dev nasm \
        graphviz python3 python3-dev qtbase5-dev libkf5coreaddons-dev \
        libkf5i18n-dev libkf5config-dev libkf5windowsystem-dev libkf5kio-dev \
        libqt5x11extras5-dev autoconf libcups2-dev libfontconfig1-dev gperf \
        openjdk-17-jdk doxygen libxslt1-dev xsltproc libxml2-utils libxrandr-dev \
        libx11-dev bison flex libgtk-3-dev libgstreamer-plugins-base1.0-dev \
        libgstreamer1.0-dev ant ant-optional libnss3-dev libavahi-client-dev libxt-dev
# clean up the apt cache to reduce the image size
RUN rm -rf /var/lib/apt/lists/*

# TODO: For some reason, autogen.sh does not like GIT_TAG and BUILD_TYPE environment variables
#       when they are used in the RUN command below. Therefore, we need to unset them before running
#       autogen.sh. This is a temporary workaround until we find a better solution.
#
#   For reference the error message from autogen.sh is:
#
#    configure: error: You have sourced config_host.mk in this shell.
#    This may lead to trouble, please run in a fresh (login) shell.
#    Error running configure at ./autogen.sh line 321.
#
RUN git_tag_value="${GIT_TAG}" && \
    build_type_value="${BUILD_TYPE}" && \
    unset GIT_TAG && unset BUILD_TYPE && \
    mkdir -p /root/libreoffice && \
    git clone "https://git.libreoffice.org/core" /root/libreoffice/core && \
    cd /root/libreoffice/core && \
    git fetch --tags && \
    git checkout tags/"$git_tag_value" -b "$git_tag_value" && \
    if [ "$build_type_value" = "debug" ]; then ./autogen.sh --enable-debug; else ./autogen.sh; fi && \
    make


# ----------------------------------------
# Stage 2: Create final image
# ----------------------------------------
FROM ubuntu:23.10
SHELL ["/bin/bash", "-c"]

# Replace default mirror with an alternative mirror
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.dotsrc.org/ubuntu/|g' /etc/apt/sources.list


# Install the runtime dependencies
# NOTE: x11-xserver-utils is needed for the using the hosts X server to run libreoffice
ENV TZ=Europe/Oslo
RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        build-essential curl g++ git \
        vim sudo wget cmake tzdata pkg-config \
        graphviz python3 python3-dev python3-pip python3-uno \
        libgtk-3-dev libcanberra-gtk-module \
        openjdk-17-jdk xsltproc libxml2-utils

RUN pip install --break-system-packages Flask

# clean up the apt cache to reduce the image size
RUN rm -rf /var/lib/apt/lists/*

ARG user=docker-user
ARG home=/home/$user

# Add user and set up sudo
RUN useradd --create-home -s /bin/bash $user \
        && echo $user:ubuntu | chpasswd \
        && adduser $user sudo \
        && echo "$user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

COPY --from=builder /root/libreoffice/core/instdir $home/libreoffice/instdir
RUN chown -R $user:$user $home/libreoffice
COPY --chown=$user:$user container/* $home/

WORKDIR $home

ENV USER=$user
ENV SHELL=/bin/bash
USER $user

CMD ["./start.sh"]

