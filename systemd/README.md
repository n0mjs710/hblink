Copy required service file into /lib/systemd/system
To make the network-online.target available (required by HB service files)
systemctl enable systemd-networkd-wait-online.service


Example HB confbridge service

Enable the service at boot
systemctl enable hb_confbridge.service

Check the status of the service
systemctl status hb_confbridge.service

Start the service if stopped
systemctl start hb_confbridge.service

Restart the service
systemctl restart hb_confbridge.service

Stop the service if running
systemctl stop hb_confbridge.service

Disable starting the service at boot
systemctl disable hb_confbridge.service
