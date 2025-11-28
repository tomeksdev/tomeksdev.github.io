---
layout: project
title: Donauwörth Datacenter Build-Out
date: 2024-09-17
summary: Constructed and configured a state-of-the-art datacenter in Donauwörth with high-speed networking, resilient routing, and powerful compute clusters for internal and customer use.
tags: [Datacenter, Networking, Infrastructure]
---

1. Routing and Connectivity:
 - BGP routers placed in two separate telecom rooms, each with 3× 1G BGP connections.
 - Spine switches located in two separate patch rooms, connected to BGP routers using LACP with 2× 40G uplinks each.
 - 10× Leaf switches connected via LACP to each Spine with 2× 100G uplinks per connection.
2. Management Access:
 - 9× Aruba 6100 12G CL4 2SFP+ switches for management, connected to Leaf switches with 2× 10G LACP uplinks.
3. Security and Firewall:
 - 2× Sophos XGS4500 in HA mode for internal infrastructure with dual 10G LACP uplinks.
 - 1× Sophos XGS2100 with 2× 10G LACP uplinks dedicated to customer traffic.
4. Compute and Storage:
 - 4× Dell PowerEdge R7550 servers for a new customer cluster, each with dual-port 25G LACP.
 - 1× Dell EMC ME5024 with extension unit, equipped with SSD SAS disks.
 - 1× Dell EMC ME5024 with 4 extension units, fully populated with 15K SAS disks.
 - 4× HPE DL380 Gen11 servers for a second cluster, each configured with 2× 25G LACP ports.
 - 1× HPE MSA 2060 for internal workloads, using SSD SAS drives.
 - 1× Synology HD6500 with extension unit providing 2PB storage, connected via 2× 25G uplinks for backup.