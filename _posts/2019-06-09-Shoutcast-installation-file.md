---
layout: post
title: Shoutcast installation file
description: Small script to install shoutcast server with all commands in few lines
imgAlt: Shoutcast
imageBig: shoutcast.png
imageSmall: shoutcast.png
keywords: shoutcast, radio, stream, server, installation, script, bash, ubuntu, debian, linux, DDNAS, v1, v2, stream, password
---

*![Alt]({{ baseurl }}/postImages/Shoutcast_1.png "Shoutcast")*

For private and business purposes, I made the installation script for the shoutcast server 64-bit. The script installs the latest version of the shoutcast server that is released, and includes a **_DDNAS_** certificate for the installation so that the server supports v1 and v2 shoutcasts. Also, the script performs and creates an automatic startup of the shoutcast server when booting the system up and has a simple command for easier shoutcast server control.

Installation is done in just three simple commands.

You will need to download the installation file from the page [TomeksDEV](https://tomeksdev.com/tools/linux/shoutcast-inst.tar.gz) and unzip the same file.

```
wget https://github.com/tomeksdev/tomeksdev.github.io/raw/master/tools/linux/shoutcast-inst.tar.gz
tar xfz shoutcast-inst.tar.gz
sudo ./shoutcast-inst
```

When installing, you will be asked to enter 4 passwords (adminpassword, password, streamadminpassword_1, streampassword_1) and IPs that will be stored in the sc_serv.conf file that will serve us for the Shoutcast server.

NOTE: The **_adminpassword_** and **_password_** can not be the same, and it's best to have **_streamadminpassword_** and **_streampassword_** different from each other.

Test:

- Ubuntu 18.04 LTS - `WORKING`

- Ubuntu 18.04 Desktop - `WORKING`

- Ubuntu 16.04 LTS - `WORKING`

- Ubuntu 16.04 Desktop - `WORKING`

- Debian 8 Jessie - `WORKING`

- Debian 9 Stretch - `WORKING`

- Debian 10 Buster - `WORKING`



Command usage:

```
shoutcast { start | stop | restart }
```