If node have SAS controller wich is extern and connected with extern storage(example MSA 1060 SAS) we must first change some lines in iscsid.conf file.

``# nano /etc/iscsi/iscsid.conf``

Search for two lines and change like its writen bellow.

````
node.startup = automatic
node.session.timeo.replacement_timeout = 15
````

After we change iscsid.conf file, we can make update of system, and if its needed also apt upgrade and for this solution to work, install new service called multipath.

``# apt-get update -y && apt-get install -y multipath-tools``

When service is installed we must get WWID from disk drives what was showed with lsblk command and what was linux node readerd from storage node.

``# lsblk``
Input looks like that before storage is coonected, and after looks something like that, depends on how many luns we created on storage.

To see and know WWID from drive wich must be in multipath, we use command bellow but always change 'X' variable to name what we see on lsblk.

``# /lib/udev/scsi_id -g -u -d /dev/sdX``

Copy this WWID to some text editor that you have always by yourselfs because we needed this id to configure multipath.conf file.

Now, when we have WWID we can create multipath.conf file and make configuration for all disk drives wich are goes to same multipath.

``# nano /etc/multipath.conf``

Copy/paste this config and only put your WWID. If you need more, just add more same lines like in config.
````
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
````

Now we are finis with config file of multipath and must only add to multipath to recognize all with command bellow(repeat this how much diffirent WWID'S you have).

``# multipath -a WWID``

After you make all we need to restart multipath service.

``# systemctl restart multipath-tools.service``

You can check all multipath devices with command bellow.

``# multipath -ll``

After all configuration run command bellow in order.

``# multipath -v3``
``# multipath -v2 -d``
``# multipathd reconfigure``
``# init 6``

Problem in Proxmox node is that they cannot see this drive normaly, and because of that, we must manualy create volume group and LVM group in order for each disk drive on WWID that we will be able to create storage for virtual machines after in Proxmox GUI. Variable X here is number what is recommended and you can user from 0 and above for each WWID.

``# pvcreate /dev/mapper/mpathX``
``# vgcreate qdisk-vg /dev/mapper/mpathX``