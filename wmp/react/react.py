from scapy.all import *
import getopt, sys
import time
import json
import netifaces
import re
import signal

import string, random
import glob

neigh_list = {};
ieee80211_stats={}
ieee80211_stats_={}
C=1
CLAIM_CAPACITY=0.8
mon_iface="mon0"
t_tx=float(time.time())
debug=False
react_count=0

cw_=15
cw=cw_


MAX_THR=5140 #kbps
rate=0; #APP RATE

"""
REACT INIT
"""
def init(iface):
	global my_mac;
	my_mac=str(netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr'])
	setCW(1,2,15,1023,0)
	init_pkt={};
	init_pkt['t']=0
	init_pkt['offer'] = C
	init_pkt['claim'] = 0
	init_pkt['w'] = 0

	neigh_list[my_mac]=init_pkt


"""
get PHY name for current device
"""
def getPHY():
	devs_info = subprocess.Popen(["iw","dev"], stdout=subprocess.PIPE).communicate()[0]
	pp=str.split(str(devs_info),'\n')
	#phy = subprocess.Popen(["ls", "/sys/kernel/debug/ieee80211/"], stdout=subprocess.PIPE).communicate()[0]
	phy=pp[0].replace("#","")
	return phy

"""
get iee80211 debugfs packet informations
current format of iee80211_stats:
{'failed_count': 0, 'dot11FCSErrorCount': 3, 'dot11RTSSuccessCount': 0, 'dot11TransmittedFrameCount': 1, 'dot11ACKFailureCount': 0, 'retry_count': 0, 'multiple_retry_count': 0, 'received_fragment_count': 30, 'frame_duplicate_count': 0, 'transmitted_fragment_count': 1, 'multicast_dot11TransmittedFrameCount': 1, 'multicast_received_frame_count': 20, 'dot11RTSFailureCount': 0}
"""
def get_ieee80211_stats(iface):
#	out = subprocess.Popen(["./ieee_stats.sh","-v"], stdout=subprocess.PIPE).communicate()[0]
	phy=getPHY();
	out = subprocess.Popen(["bash","ieee_stats.sh",phy], stdout=subprocess.PIPE).communicate()[0]
	ieee80211_stats_diff=json.loads(str(out))
	return ieee80211_stats_diff

#TODO: follow approach seems to be too slow and grab wrong values
"""
	phy=getPHY();
	#stats_path="/sys/kernel/debug/ieee80211/phy{}/statistics/*".format(str.split(phy)[-1])
	stats_path="/sys/kernel/debug/ieee80211/{}/statistics/*".format(str.split(phy)[-1])

	i=0
	stats_file_list=glob.glob(stats_path)
	f={}
	ieee80211_stats_diff={}
	for ff in stats_file_list:
#		key=str.split(ff,"/")[-1]
		f[i] = open(ff, 'r')
		i+=1;

	for i in range(0,len(f)):
		key=str.split(stats_file_list[i],"/")[-1]
		val=int(f[i].read())
		ieee80211_stats[key]=val
	
	if ieee80211_stats_ :
		for key in ieee80211_stats:
			ieee80211_stats_diff[key]=ieee80211_stats[key]-ieee80211_stats_[key]
			ieee80211_stats_[key]=ieee80211_stats[key]
	else:
		for key in ieee80211_stats:
			ieee80211_stats_[key]=ieee80211_stats[key];
	return ieee80211_stats_diff
"""

"""
Compute txtime theoretical value for given:
% Input vars:
%   v80211  : '11b', '11g', '11a' or '11p'
%   bitrate : 1,2,5.5,11,6,9,12,18,24,36,48,54
%   bw      : 20,10,5
%   pkt_size: value in byte
% NOTE: pkt_size means  MAC_H + LLC_H  + PAYLOAD + MAC_FCS
"""

def txtime_theor(v80211,bitrate,bw,pkt_size):
    Tpre=16*20/bw;
    Tsig=4*20/bw;
    Tsym=4*20/bw;
    l_ack=14;
    l_rts=20;
    tx_time_theor=0
    if v80211 == '11b':
            CWmin=15;
            tslot=20;
            SIFS=10;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;         
            t_ack=192+l_ack*28/bitrate+1;
            t_rts=192+l_rts*28/bitrate+1;
            tx_time_theor=192+(pkt_size+28)*8/bitrate+1;
            rate=bitrate;
            
            
    elif v80211 == '11g':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=9;
            SIFS=16;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;        
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/rate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/rate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate); 
            

    elif v80211 == '11a':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=9;
            SIFS=16;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/bitrate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/bitrate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate);
            
    elif v80211 == '11p':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=13;
            SIFS=32;
            AIFS=2;
            DIFS=AIFS*tslot+SIFS;
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/bitrate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/bitrate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate);

    return [tslot, tx_time_theor, t_rts] 
	
def update_cw(iface,i_time,enable_react,sleep_time):
	while True:
		if 1:
			update_cw_decision(iface,enable_react,sleep_time);
		time.sleep(sleep_time)

"""
Set CW
"""

def setCW(qumId,aifs,cwmin,cwmax,burst):

#       echo "0 1 1 3 0" > /sys/kernel/debug/ieee80211/phy0/ath9k/txq_params
#
#       Proper sequence is : "qumId aifs cwmin cwmax burst"

	phy=getPHY();	
	
	f_name='/sys/kernel/debug/ieee80211/{}/ath9k/txq_params'.format(phy);
	txq_params_msg='{} {} {} {} {}'.format(qumId,aifs,cwmin,cwmax,burst)
	f_cw = open(f_name, 'w')
	f_cw.write(txq_params_msg)	

"""
update CW decision based on ieee80211 stats values and virtual channel freezing estimation
"""
def update_cw_decision(iface,enable_react,sleep_time):
	#get stats
	global my_mac
	global cw
	global cw_
	CWMIN=15
	CWMAX=2047
	pkt_stats=get_ieee80211_stats(iface)
	pkt_size=1534
	if pkt_stats:
		tx_goal=0
		I=0
		dd = sleep_time;

                gross_rate = float(CLAIM_CAPACITY)*float(neigh_list[my_mac]['claim']);
		#data_count = pkt_stats['dot11TransmittedFrameCount']-2
		data_count = pkt_stats['dot11RTSSuccessCount']
		rts_count = pkt_stats['dot11RTSSuccessCount'] + pkt_stats['dot11RTSFailureCount']

                busytx2 =  0.002198*float(data_count) + 0.000081*float(rts_count); #how much time the station spent in tx state during the last observation internval
		SIFS=16 #usec
		tslot=9e-6 #usec
                freeze2 = dd - busytx2 - cw_/float(2)*tslot*rts_count - 2*SIFS*1e-6; #how long the backoff has been frozen;
		if rts_count > 0:
			avg_tx = float(busytx2)/float(rts_count); #average transmission time in a transmittion cycle
			psucc = float(data_count)/float(rts_count);
		else:
			avg_tx=0
			psucc=0

		if avg_tx > 0:
			tx_goal = float(dd*gross_rate)/float(avg_tx);
		else:
			tx_goal = 0

                freeze_predict = float(freeze2)/float(dd-busytx2)*float(dd-dd*float(gross_rate))  ;


		if tx_goal > 0:
			cw = 2/float(0.000009) * (dd-tx_goal*avg_tx-freeze_predict)/float(tx_goal);


		if cw < CWMIN: 
			cw_=CWMIN
		elif cw > CWMAX:
			cw_=CWMAX
		else:
			cw_=cw
			#alpha=0.7
			#cw_ = (alpha * cw_ + (1-alpha) * cw );
		
		# ENFORCE CW

		qumId=1 #BE
		aifs=2
		cwmin=int(cw_);
		cwmax=int(cw_);
		burst=0
		if enable_react:
			setCW(qumId,aifs,cwmin,cwmax,burst);
               	thr=(pkt_stats['dot11RTSSuccessCount'])*1470*8/1e6; 
		#print "dt={},data_count={},rts_count={},tx_time_theor={},t_rts={},busytx2={},gross_rate={},avg_tx={},freeze_predict={},tx_goal={},I={},cw={},cw_={},thr={}".format(
		#	dt,data_count,rts_count,tx_time_theor,t_rts,busytx2,gross_rate,avg_tx,freeze_predict,tx_goal,I,cw,cw_,thr)
		print "dd=%.4f data_count=%.4f rts_count=%.4f busytx2=%.4f gross_rate=%.4f,avg_tx=%.4f freeze2=%.4f freeze_predict=%.4f tx_goal=%.4f I=%.4f cw=%.4f cw_=%.4f pscc=%.4f" % (dd,data_count,rts_count,busytx2,gross_rate,avg_tx,freeze2,freeze_predict,tx_goal,I,cw,cw_,psucc)



def updateAction(iface,i_time):
  # uploadPacket function has access to the url & token parameters because they are 'closed' in the nested function
	def uploadPacket(packet):
		global my_mac
		global t_tx
		global react_count
		try:
				
			if str(packet.addr2) == my_mac:
			#TX
				pass;
			else:
				if 'claim' in str(packet[2]):
					payload='{'+re.search(r'\{(.*)\}', str(packet[2]) ).group(1)+'}'
					curr_pkt=json.loads(payload)
			#RX
				
					neigh_list[str(packet.addr2)]=curr_pkt;
					curr_pkt['t'] = float(time.time())
					update_offer();
					update_claim()
							
		except Exception, err:
			if debug:
				print Exception, err           
			pass
	return uploadPacket
def update_offer():
	done = False;
	A = C;
	global my_mac
	D = [key for key,val in neigh_list.items()]
	Dstar=[];	
	while done == False:
		Ddiff=list(set(D)-set(Dstar))
		if set(D) == set(Dstar):
			done = True
			neigh_list[my_mac]['offer'] = A + max([val['claim'] for key,val in neigh_list.items()]) 
		else:
			done = True
			neigh_list[my_mac]['offer'] = A / float(len(Ddiff)) 
			for b in Ddiff:
				if neigh_list[b]['claim'] < neigh_list[my_mac]['offer']:
					Dstar.append(b)
					A -= neigh_list[b]['claim']
					done = False	
def update_claim():
	off_w=[val['offer'] for key,val in neigh_list.items()]
	off_w.append(neigh_list[my_mac]['w'])
	neigh_list[my_mac]['claim']=min(off_w)

def sniffer_REACT(iface,i_time):
	sniff(iface=mon_iface, prn=updateAction(iface,i_time))

def send_ctrl_msg(iface,json_data):
        #a=Ether(dst="ff:ff:ff:ff:ff:ff",src=my_mac)/Dot1Q(prio=5)/json_data
        a=RadioTap()/Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=my_mac, addr3="ff:ff:ff:ff:ff:ff")/json_data
        #hexdump(a)
        sendp(a, iface=mon_iface,verbose=0)

def send_REACT_msg(iface,i_time,iperf_rate):
	#TX
	global my_mac
	my_mac=str(netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr'])
	while True:
		if 1:
			rate = min((long)( C ),( (iperf_rate*C)/float(MAX_THR)) );
			neigh_list[my_mac]['w']=rate
	
			#print neigh_list
			try:
				pkt_to_send={};
	
				neigh_list[my_mac]['t']=float(time.time())
				pkt_to_send['t']=neigh_list[my_mac]['t']
				pkt_to_send['claim']=neigh_list[my_mac]['claim']
				pkt_to_send['offer']=neigh_list[my_mac]['offer']
				#pkt_to_send['w']=neigh_list[my_mac]['w']
				json_data = json.dumps(pkt_to_send)
				
				#check dead nodes
				timeout = i_time * 5
				
				for key,val in neigh_list.items():
					if float(time.time())-val['t'] > timeout:
						neigh_list.pop(key)
						update_offer()
						update_claim()
				
				# REACT variables updated, transmit!
				send_ctrl_msg(iface,json_data)

			except Exception, err:
				if debug:
					print Exception, err           
				pass

		time.sleep(i_time)

def usage(in_opt,ext_in_opt):
	print("input error: here optionlist: \n{0} --> {1}\n".format(in_opt,str(ext_in_opt)))

def main():
	ext_in_opt=["help", "iface=","tdelay=", "iperf_rate=", "enable_react="];
	in_opt="hi:t:r:e"	
	try:
	    opts, args = getopt.getopt(sys.argv[1:], in_opt, ext_in_opt)
	except getopt.GetoptError as err:
	    # print help information and exit:
	    print str(err)  # will print something like "option -a not recognized"
	    usage(in_opt,ext_in_opt)
	    sys.exit(2)
	i_time=0;
	iface='wlan0';
	iperf_rate=0;
	enable_react=False
	for o, a in opts:
	    if o in ("-i", "--iface"):
		iface = a
	    if o  in ("-t", "--tdelay"):
	       i_time = float(a)
	    if o  in ("-r", "--iperf_rate"):
	       iperf_rate = float(a)
	    if o  in ("-e", "--enable_react"):
	       enable_react=True
	    elif o in ("-h", "--help"):
		usage()
		sys.exit()
	#INIT REACT INFO
	init(iface);
	try:
		#thread cw update???
		thread.start_new_thread( update_cw,(iface,i_time,enable_react,1) )		

		#Thread transmitter
		thread.start_new_thread( send_REACT_msg,(iface,i_time,iperf_rate ) )

		#thread receiver
		thread.start_new_thread( sniffer_REACT,(iface,i_time ) )

	except Exception, err:
		print err
		print "Error: unable to start thread"

	while 1:
	   pass
	
		    
	
if __name__ == "__main__":
    main()
