---
layout: post
title: Wireguard and iptables firewall
description: Tutorial about extending firewall/security of Wireguard VPN server from unwanted traffic
imageBig: TomeksDEV-blog.png
imageSmall: TomeksDEV-blog-small.png
keywords: linux, ubuntu, debian, wireguard, vpn, connection, security, protocol, server, iptables, firewall
---
In this post we will have look at security of wireguard VPN server and iptables in linux. Before i was write post about installation of Wireguard VPN server with GUI which you can find HERE or on my github project HERE.
Bellow is little tutorial how to extend this installation with security/firewall settings that your server is protected from unwanted traffic.

### What are IPTABLES?
---------------------------------------------

Iptables is a Linux firewall management tool that controls network traffic by defining rules. It filters, NATs, tracks connections, mangles packets, logs events, and enhances server security. It's crucial for managing access, protecting against threats, and directing network traffic. It uses tables, chains, and command-line commands for configuration and requires root privileges. Note that nftables is its modern successor on some Linux distributions.

### Creating and managing iptables rules
---------------------------------------------

My suggestion is to manage iptables with multiple files, and thats because in my deployment, i have many and many rules where and who can access to which network, server, applications.

For that i make default file which than load on every start/reboot of wireguard VPN server and GUI.
In this file than i include others files in which i write allowed access and what can do. Offcourse, i have one default file where are rules which needed to be apply for all. Next thing, i make rules file for each VPN connection separate that i can have better look and better controll over others accessing to some servers, application.

#### Step 1:

We need to create default file that will be loaded in Wireguard GUI and include all other files what we need.

```
touch /etc/iptables/rules.ipv4
```

I also created separated files default.v4, input_default_rules.v4, output_default_rules.v4 and nat_rules.v4

```
touch /etc/iptables/default.ipv4
touch /etc/iptables/input_default_rules.ipv4
touch /etc/iptables/output_default_rules.ipv4
touch /etc/iptables/nat_rules.ipv4
```
I like to have separated files because of many of rules what i include in iptables.
We can also add file for WG-Client which is connection to server input for each client and also output file for each client.

#### Step 2:

Now we created all files what we need and can start filling them what all we need. I believe that most what we need is SSH, ICMP, Wireguard WebGUI port and Wireguard VPN port, everything else is here not needed if you dont have anything more.

In file default.v4 i put only start of iptables like bellow.

```
# IPTables Rules
*filter
:INPUT DROP [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT DROP [0:0]
```

After in file input_default_rules.v4 i put all incoming traffic rules what i allow.

```
# Input rules
-A INPUT -i lo -j ACCEPT
## SSH
-A INPUT -s WIREGUARD_PRIVATE_NETWORK -p tcp -m tcp --sport 513:65535 --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT
## Wireguard
-A INPUT -s WIREGUARD_PRIVATE_NETWORK -p tcp --dport 5000 -m state --state NEW,ESTABLISHED -j ACCEPT
-A INPUT -d WIREGUARD_PUBLIC_IP/32 -p udp -m udp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
## ICMP
-A INPUT -d WIREGUARD_PRIVATE_NETWORK -p icmp -m state --state NEW,ESTABLISHED -j ACCEPT
-A INPUT -i eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -j DROP
```

This is standard rules where i like to allow ssh only from Wireguard private network, who is connected to VPN only. Also for ICMP and access to WebGUI. Only allowed traffic from outside is on port 443 which i have for VPN port and connection to my Wireguard server. You can put here port which you choose for yours wireguard server.

Output rules looks simmilar to input but in diffirent way in file output_default_rules.v4

```
# Output rules
-A OUTPUT -o lo -j ACCEPT
## SSH
-A OUTPUT -d WIREGUARD_PRIVATE_NETWORK -p tcp -m tcp --sport 22 --dport 513:65535 -m state --state ESTABLISHED -j ACCEPT
## Wireguard
-A OUTPUT -d WIREGUARD_PRIVATE_NETWORK -p tcp --sport 5000 -m state --state ESTABLISHED -j ACCEPT
-A OUTPUT -s WIREGUARD_PUBLIC_IP/32 -p udp -m udp --sport 443 -m state --state ESTABLISHED -j ACCEPT
## ICMP
-A OUTPUT -s WIREGUARD_PRIVATE_IP/32 -p icmp -m state --state ESTABLISHED -j ACCEPT
-A OUTPUT -o eth0 -d 0.0.0.0/0 -j ACCEPT
-A OUTPUT -j DROP
COMMIT
```

And after that i have added last line of nat rules inf file nat_rules.v4

```
# NAT Rules
*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -o eth0 -j MASQUERADE
COMMIT
```

Other files you can write in yours wish and what all you need, like for example wg_client1_rules.v4 where you can write to what and where this user have access, or whole network from this client.

#### Step 3:

After that i create one script which than load all my iptables rules in one file, rules.v4 which is than loaded to iptables. For that i use cat command and include inside all files which i want to put in iptables.

```
mkdir /opt/iptables
touch /opt/iptables/import_iptables.sh
chmod +x /opt/iptables/import_iptables.sh
```

After i created and give exe rights to script than i add all files created in step before.

```
#!/bin/bash

# Import all imported files from iptables rules
cat /etc/iptables/default.v4 /etc/iptables/input_default_rules.v4 /etc/iptables/output_default_rules.v4 /etc/iptables/nat_rules.v4 > /etc/iptables/rules.v4
# Activate iptables from file
iptables-restore < /etc/iptables/rules.v4
```

#### Step 4:

When you finished with rules and all what you need, now is last step to load all in wireguard GUI.

This can be doned that in setting of wireguard GUI under "Wireguard Server" settings change "PostUp Script" and write this line which loads all iptables rules.

```
iptables-restore < /etc/iptables/rules.ipv4
```

And if you stop wireguard server, you can write only this bellow in "PostDown Script" that you can flush all rules.

```
iptables -F
```

And after that, you can restart wireguard server or only make interface of wireguard down and up.

```
sudo wg-quick down wg0    # Take the interface down
sudo wg-quick up wg0      # Bring the interface back up
```

### Conclusion
----------------------------------------------
