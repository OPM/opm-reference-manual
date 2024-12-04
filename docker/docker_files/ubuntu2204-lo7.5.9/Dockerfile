FROM ubuntu:22.04
SHELL ["/bin/bash", "-c"]

RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.dotsrc.org/ubuntu/|g' /etc/apt/sources.list

# Install the runtime dependencies
# NOTE: x11-xserver-utils is needed for the using the hosts X server to run libreoffice
ENV TZ=Europe/Oslo
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        software-properties-common
# NOTE: it is important to use libreoffice-still (not libreoffice-fresh or ppa)
#  libreoffice-still gives version 7.5 (whereas libreoffice-fresh gives version 7.6)
RUN add-apt-repository ppa:libreoffice/libreoffice-still && apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        curl git vim sudo wget tzdata \
        x11-xserver-utils
RUN apt-get install -y libreoffice
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-uno libreoffice-dev
RUN pip install Flask

# clean up the apt cache to reduce the image size
RUN rm -rf /var/lib/apt/lists/*

ARG user=docker-user
ARG home=/home/$user

# Add user and set up sudo
RUN useradd --create-home -s /bin/bash $user \
        && echo $user:ubuntu | chpasswd \
        && adduser $user sudo \
        && echo "$user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

COPY --chown=$user:$user container/* $home/
RUN chmod +x $home/start.sh
RUN chmod +x $home/update-libreoffice-config.sh

# Switch to the $user or else .config will be created as root
USER $user
# Create the $home/.config directory and extract the libreoffice-config.tar.gz file into it
RUN mkdir -p $home/.config && \
    tar -xzf $home/libreoffice-config.tar.gz -C $home/.config && \
    rm $home/libreoffice-config.tar.gz
USER root
WORKDIR $home

ENV USER=$user
ENV SHELL=/bin/bash
USER $user

CMD ["./start.sh"]

