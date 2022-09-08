We are looking and investigating the connection between proxmox and SAS storage. In our case we are using two HPE DL380 Gen10 servers and one MSA 2060 SAS LFF storage. During our investigation and research, we came across the Multipath configuration that needs to be configured on Linux machines in order for the SAS to work normally and without any issues. Therefore, we made an effort to configure Multipath and successfully make all luns visible and add them to our nodes. Below is an explanation of how we got this solution to work. 

![Alt](https://tomeksdev.com/new/postImages/proxmox_sas_small.svg "Proxmox")

If the node has a SAS controller that is external and connected to external storage (e.g. MSA 1060 SAS), we first need to change some lines in the iscsid.conf file.


        # nano /etc/iscsi/iscsid.conf

Search for two lines and change like its writen bellow.

        node.startup = automatic
        node.session.timeo.replacement_timeout = 15

After changing the iscsid.conf file, we must update the system (if necessary, also install ``apt upgrade``), for this solution to work, and install new service called multipath.

        # apt-get update -y && apt-get install -y multipath-tools

When service is installed we must get WWID from disk drives what was showed with lsblk command and what was linux node readerd from storage node.

        # lsblk

Input looks like that before storage is coonected, and after looks something like that, depends on how many luns we created on storage.

To see and know WWID from drive wich must be in multipath, we use command bellow but always change 'X' variable to name what we see on lsblk.

        # /lib/udev/scsi_id -g -u -d /dev/sdX

![Alt](https://tomeksdev.com/new/postImages/proxmox_wwid.png "Proxmox")

Copy this WWID to some text editor that you have always by yourselfs because we needed this id to configure multipath.conf file.

Now, when we have WWID we can create multipath.conf file and make configuration for all disk drives wich are goes to same multipath.

        # nano /etc/multipath.conf

Copy/paste this config and only put your WWID. If you need more, just add more same lines like in config.

        blacklist {
                wwid .*
        }

        blacklist_exceptions {
                wwid "WWID"
                wwid "WWID"
        }

        multipaths {
        multipath {
                wwid "WWID"
                alias mpath0
        }
        multipath {
                wwid "WWID"
                alias mpath1
        }
        }
        defaults {
                polling_interval        2
                path_selector           "round-robin 0"
                path_grouping_policy    multibus
                uid_attribute           ID_SERIAL
                rr_min_io               100
                failback                immediate
                no_path_retry           queue
                user_friendly_names     yes
        }

Now we are finis with config file of multipath and must only add to multipath to recognize all with command bellow(repeat this how much diffirent WWID'S you have).

        # multipath -a WWID

After you make all we need to restart multipath service.

        # systemctl restart multipath-tools.service

You can check all multipath devices with command bellow.

        # multipath -ll

![Alt](https://tomeksdev.com/new/postImages/proxmox_multipath.png "Proxmox")

After all configuration run command bellow in order.

        # multipath -v3
        # multipath -v2 -d
        # multipathd reconfigure
        # init 6

The problem in the Proxmox node is that they usually can't see this drive and for this reason we need to manually create a volume group and an LVM group for each drive on the WWID after which we will be able to create virtual machine storage in the Proxmox GUI. The variable X is a recommended number here and you can use a value of 0 and higher for each WWID.

        # pvcreate /dev/mapper/mpathX
        # vgcreate qdisk-vg /dev/mapper/mpathX

In summary, we are using this server in production and so far we have no problems with memory and nothing. It is important to take this step and configure Multipath because if it is not configured, you will have several problems with memory for VMs and containers.
