---
layout: post
title: Install and configure qDevice for Proxmox quorum
description: Configure QDevice for Proxmox 8 in Synology NAS Docker
imageBig: qdevice-docker.png
imageSmall: qdevice-docker-small.png
keywords: linux, servers, technology, hardware, learning, virtualization, synology, NAS, docker, proxmox
---
First, we must install Docker service on Synology NAS. After installation, you need to allow SSH to Synology and then make an SSH connection to Synology. This Docker is on the same network as Synology but uses a separate network IP because Proxmox needs SSH login to the Quorum device. When you are logged into Synology, you can manually enter the commands below as written.

You can change your location as you will, but I used this location:

```
# mkdir -p /volume1/docker/qnetd/corosync-data
```

After that, change your location to:

```
# cd /volume1/docker/qnetd/
```

We must create a Dockerfile to make an image that will bring up the Docker container. Also, here we automatically install all needed services for QDevice. Copy/Paste the code below into the Dockerfile.

```
# vi Dockerfile
```

```
FROM debian:bullseye
RUN echo 'debconf debconf/frontend select teletype' | debconf-set-selections
RUN apt-get update
RUN apt-get dist-upgrade -qy
RUN apt-get install -qy --no-install-recommends systemd systemd-sysv corosync-qnetd openssh-server
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/* /var/log/alternatives.log /var/log/apt/history.log /var/log/apt/term.log /var/log/dpkg.log
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo 'root:password' | chpasswd
RUN systemctl mask -- dev-hugepages.mount sys-fs-fuse-connections.mount
RUN rm -f /etc/machine-id /var/lib/dbus/machine-id

FROM debian:bullseye
COPY --from=0 / /
ENV container docker
STOPSIGNAL SIGRTMIN+3
VOLUME [ "/sys/fs/cgroup", "/run", "/run/lock", "/tmp" ]
CMD [ "/sbin/init" ]
```
We must build the Docker image, and we can do this with the command below. This can take some time, and if you want, you can make coffee yourself. :)

```
# docker build . -t debian-qdevice
```

Here we create a network for Docker so that we can create a separate IP in the same network as Synology for this Docker, allowing Proxmox nodes to have access over SSH. Change the IP and gateway depending on which network you are located.

```
# docker network create -d macvlan \
    --subnet=192.168.192.0/24 \
    --gateway=192.168.192.1 \
    -o parent=eth0 \
    macvlan-net
```

Now we need to bring the container up, but first, we need to allocate a static IP for this Docker and also allocate volumes. Also, here change the IP which is not taken in your network.

```
# docker run -d -it \
    --name qnetd \
    --net=macvlan-net \
    --ip=192.168.192.27 \
    -v /volume1/docker/qnetd/corosync-data:/etc/corosync \
    -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
    --restart=always \
    debian-qdevice:latest
```

When the Docker is up and running, we need to SSH into this container. All is allowed so that you can SSH without a problem. When we are logged in, we must enter the command to change permissions on the /etc/corosync/ folder. We must change the owner of the folder with the command below.

```
# chown -R coroqnetd:coroqnetd /etc/corosync/
```

Then you can reboot and see if the service starts after reboot.

```
# init 6
```

With this command, you make sure that the service qnetd is running and functioning.

```
# ps auxf
```

If all works as written here, then you can join the QDevice to the Proxmox host and you have successfully set up a quorum device on Synology and have an HA cluster with a 2-node Proxmox cluster and storage. The command to join the cluster is executed on the Proxmox node:

```
# pvecm qdevice setup 192.168.192.27 -f
```

After that, you can check the status of the cluster with the command below and see if QDevice gives a vote to the HA cluster.

```
# pvecm status
```

### Conclusion
----------------------------------------------
Setting up a QDevice for Proxmox 8 in a Synology NAS Docker environment involves several steps, including installing Docker on Synology, configuring SSH access, and creating and deploying a Docker image tailored for the quorum device. By following the outlined procedures, you can achieve a functional and reliable QDevice setup, enhancing the high availability (HA) of your Proxmox cluster.

Key steps include:
1. **Installing and Configuring Docker on Synology**: This includes enabling SSH access and setting up the necessary directories.
2. **Creating and Building the Docker Image**: A Dockerfile is used to build an image that includes all required services such as `corosync-qnetd` and `openssh-server`.
3. **Configuring the Docker Network**: A macvlan network ensures the Docker container has its own IP address within the same subnet as the Synology NAS.
4. **Deploying the Docker Container**: Running the container with appropriate volume mounts and network settings.
5. **Post-Deployment Configuration**: Setting correct permissions and ensuring services start as expected.

After completing these steps, the QDevice can be integrated into your Proxmox cluster, providing an additional quorum vote that is essential for maintaining cluster integrity in a 2-node setup. This setup allows for effective and resilient HA clustering, ensuring your virtual machines and services remain operational even in the event of node failures.

By meticulously following this guide, you ensure a robust and scalable HA cluster environment using Proxmox and Synology NAS, leveraging Docker to simplify and streamline the process.