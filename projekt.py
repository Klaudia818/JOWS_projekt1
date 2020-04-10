#!/usr/bin/python

'This example runs stations in AP mode'

import sys

from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.node import OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from time import sleep

def topology():
    'Create a network.'
    net = Mininet_wifi(controller=Controller, accessPoint=OVSKernelAP)

    info("*** Creating nodes\n")
     
    internet = net.addHost('internet', ip='10.0.0.1/24', position='30,30,30')
    
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01',position='10,18,0') #VoIP
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02',position='10,7,8') #VLC
    ap1 = net.addAccessPoint('ap1', ssid='Jows-proj1', channel='36', mode='ac', position='15,10,15')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:03', position='30,13,5') #VoD

    c0 = net.addController('c0', controller=Controller, ip='127.0.0.1', port=6633)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info("*** Adding Link\n")
    net.addLink(ap1, internet)
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap1)

    info("*** Starting network\n")
    net.build()
    c0.start()
    ap1.start([c0])
    
    net.pingFull()
    
    #Konfiguracja transmisji w kierunku UL, czyli sta1 i sta3
    sleep(5)
    ap1.cmd("tc qdisc add dev ap1-eth2 root handle 1: htb default 20")
    ap1.cmd("tc class add dev ap1-eth2 parent 1: classid 1:1 htb rate 125kbps ceil 125kbps")
    ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:10 htb rate 90kbps ceil 125kbps") #Sta1
    ap1.cmd("tc class add dev ap1-eth2 parent 1:1 classid 1:12 htb rate 35kbps ceil 125kbps") #Sta3
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.2 match ip dport 10 0xffff flowid 1:10")
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 2 u32 match ip src 10.0.0.4 match ip dport 80 0xffff flowid 1:12")
    
    #Konfiguracja transmisji w kierunku DL, czyli sta2
    internet.cmd("tc qdisc add dev internet-eth0 root handle 1: htb default 180")
    internet.cmd("tc class add dev internet-eth0 parent 1: classid 1:1 htb rate 250kbps ceil 250kbps")
    internet.cmd("tc class add dev internet-eth0 parent 1:1 classid 1:11 htb rate 180kbps ceil 250kbps") #Sta2
    internet.cmd("tc filter add dev internet-eth0 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.1 match ip dport 8080 0xffff flowid 1:11")

    #Konfiguracja portu ingressowego dla AP
    ap1.cmd("modprobe ifb")
    ap1.cmd("ip link set dev ifb0 up")
    ap1.cmd("tc qdisc add dev ifb0 root handle 1: htb default 10")
    ap1.cmd("tc qdisc add dev ap1-eth2 ingress handle ffff:")
    ap1.cmd("tc class add dev ifb0 parent 1: classid 1:1 htb rate 250kbps ceil 250kbps")
    ap1.cmd("tc class add dev ifb0 parent 1:1 classid 1:11 htb rate 180kbps ceil 250kbps")
    ap1.cmd("tc filter add dev ap1-eth2 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.1 match ip dport 8080 0xffff flowid 1:11")
 
    ap1.cmd("tc filter add dev ap1-eth2 parent ffff: protocol ip u32 match u32 0 0 action connmark action mirred egress redirect dev ifb0 flowid ffff:1")


    #Dodajemy algorytmy kolejkowania

    sleep(0.5)
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:10 handle 10: pfifo limit 5")
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:11 handle 10: pfifo limit 5")
    ap1.cmd("tc qdisc add dev ifb0 parent 1:11 handle 20: pfifo limit 5")
    ap1.cmd("tc qdisc add dev ap1-eth2 parent 1:12 handle 40: sfq perturb 10")




    #Uruchamiamy iperfa
    sleep(0.5)
    internet.cmd("iperf -s -u -p 10 -i 1 > internet_log1_2.txt &")
    #sta2.cmd("iperf -s -u -p 8080 -i 1 > internet_log2.txt &")
    internet.cmd("iperf -s -p 80 -u  -i 1 > internet_log3_2.txt &")
    internet.cmd("tcpdump -i internet-eth0 -w jows-dl.pcap &")

    sta1.cmd("iperf -c 10.0.0.1 -p 10 -t 100 -u &")
    #sta1.cmd("xterm")
    #sleep(5)
    #internet.cmd("iperf -c 10.0.0.3 -p 8080 -t 140 -u &")
    sleep(5)
    sta3.cmd("iperf -c 10.0.0.1 -p 80 -t 140 -u &")

    #sta3.cmd("gnome-terminal")
    #sleep(5)
    #internet.cmd("gnome-terminal")
    sleep(5)
    sta2.cmd("vlc-wrapper &")
    sleep(5)
    internet.cmd("vlc-wrapper &")
    sleep(10)
    #internet.cmd("xterm")


    sleep(80)
    internet.cmd("sudo killall tcpdump")

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()

