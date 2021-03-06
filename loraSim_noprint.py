#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
 LoRaSim: simulate collisions in LoRa
 Copyright © 2016 Thiemo Voigt <thiemo@sics.se> and Martin Bor <m.bor@lancaster.ac.uk>

 This work is licensed under the Creative Commons Attribution 4.0
 International License. To view a copy of this license,
 visit http://creativecommons.org/licenses/by/4.0/.

 Do LoRa Low-Power Wide-Area Networks Scale? Martin Bor, Utz Roedig, Thiemo Voigt
 and Juan Alonso, MSWiM '16, http://dx.doi.org/10.1145/2988287.2989163

 $Date: 2016-10-17 13:23:52 +0100 (Mon, 17 Oct 2016) $
 $Revision: 218 $
"""
"""
 SYNOPSIS:
   ./loraDir.py <nodes> <avgsend> <experiment> <simtime> [collision]
 DESCRIPTION:
    nodes
        number of nodes to simulate
    avgsend
        average sending interval in milliseconds
    experiment
        experiment is an integer that determines with what radio settings the
        simulation is run. All nodes are configured with a fixed transmit power
        and a single transmit frequency, unless stated otherwise.
        0   use the settings with the the slowest datarate (SF12, BW125, CR4/8).
        1   similair to experiment 0, but use a random choice of 3 transmit
            frequencies.
        2   use the settings with the fastest data rate (SF6, BW500, CR4/5).
        3   optimise the setting per node based on the distance to the gateway.
        4   use the settings as defined in LoRaWAN (SF12, BW125, CR4/5).
        5   similair to experiment 3, but also optimises the transmit power.
    simtime
        total running time in milliseconds
    collision
        set to 1 to enable the full collision check, 0 to use a simplified check.
        With the simplified check, two messages collide when they arrive at the
        same time, on the same frequency and spreading factor. The full collision
        check considers the 'capture effect', whereby a collision of one or the
 OUTPUT
    The result of every simulation run will be appended to a file named expX.dat,
    whereby X is the experiment number. The file contains a space separated table
    of values for nodes, collisions, transmissions and total energy spent. The
    data file can be easily plotted using e.g. gnuplot.
"""

import simpy
import random
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
import os

# turn on/off graphics
graphics = 0

# do the full collision check   
full_collision = False

# experiments:
# 0: packet with longest airtime, aloha-style experiment
# 0: one with 3 frequencies, 1 with 1 frequency
# 2: with shortest packets, still aloha-style
# 3: with shortest possible packets depending on distance

Link_Loss_dB = [161.6,160.7,156.6,158.5,158,154.8,156.8,152.2,154.9,153.5,151.5,151.6,152.1,152,151.9,151.8,151.4,151.2,150.4,146.8,147.3,149.8,149.3,147.8,149.2,144.4,145.9,145.2,142.8,146.4,144.5,142.5,143.2,142.8,144,145,145,144,144.8,143.4,141.1,141.4,141.9,142.6,141.6,140.1,140.9,139,140.7,140.9,139.4,139.9,140.1,138.5,140.5,138,137.1,139.2,136,139,137.8,137.9,135.9,137.3,137.4,136.1,138.1,137.1,136.7,136.2,135.1,134.8,134.3,134.4,132.9,134.1,134.9,133.9,134.2,133,133.9,133.8,130,133.6,133.1,130.5,131,132.1,132.1,131.9,130.3,132.1,129.6,129.3,129.1,128.9,128.6,129.3,128.8,128.8,124.5,127.2,124.8,126.1,125.1,124.6,122,124.4,124.4,122.8,123.4,123.1,120.9,123.4,118.1,119.1,118.5,116.9,117.3,117.6,108.7,105.3,108.2,108.8,105.6,105,103.7,100.9,99.1,96.6,96.4,95,93.9,92.3,91.8];
Ranges_km = [29.805,38.984,42.135,16.112,29.818,40.725,32.422,45.478,29.405,19.82,44.188,47.134,15.782,17.877,32.231,36.826,36.369,39.783,35.485,37.373,35.435,24.985,15.114,19.521,34.549,32.147,31.781,31.548,19.92,29.925,29.726,19.355,29.982,24.539,16.349,19.372,23.144,22.132,28.969,21.459,26.864,24.157,17.788,27.333,24.005,18.994,30.22,20.058,30.107,24.813,26.56,21.235,25.99,31.827,22.924,12.387,29.431,23.915,23.247,10.991,30.618,28.128,21.746,11.563,24.861,24.364,7.835,16.218,17.297,21.977,24.996,23.474,25.047,17.605,18.33,26.4,27.628,10.491,16.53,14.648,27.358,25.174,20.863,21.819,21.714,7.708,16.132,21.54,20.059,25.323,7.916,24.444,21.149,10.085,22.038,8.155,13.963,11.696,25.251,10.982,15.412,12.889,12.6,15.767,9.755,13.368,12.301,21.096,7.53,19.231,18.436,11.152,6.428,10.614,4.633,6.369,14.583,12.02,6.012,7.178,5.26,6.649,4.929,4.806,4.615,3.985,2.883,2.346,1.768,1.721,1.463,1.284,1.073,1.01];

max_n = len(Link_Loss_dB);


# this is an array with measured values for sensitivity
# see paper, Table 3
sf7 = np.array([7,-126.5,-124.25,-120.75])
sf8 = np.array([8,-127.25,-126.75,-124.0])
sf9 = np.array([9,-131.25,-128.25,-127.5])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.5,-132.75,-128.75])
sf12 = np.array([12,-133.25,-132.25,-132.25])

# sf6 = np.array([7,-121])
# sf7 = np.array([7,-124,-124.25,-120.75])
# sf8 = np.array([8,-127,-126.75,-124.0])
# sf9 = np.array([9,-130,-128.25,-127.5])
# sf10 = np.array([10,-133,-130.25,-128.75])
# sf11 = np.array([11,-135,-132.75,-128.75])
# sf12 = np.array([12,-137,-132.25,-132.25])

#cochannel rejection
sf7d = np.array([7, -6, 16, 18, 19, 19, 20])
sf8d = np.array([8, 24, -6, 20, 22, 22, 22])
sf9d = np.array([9, 27, 27, -6, 23, 25, 25])
sf10d = np.array([10, 30, 30, 30, -6, 26, 28])
sf11d = np.array([11, 33, 33, 33, 33, -6, 29])
sf12d = np.array([12, 36, 36, 36, 36, 36, -6])

#
# check for collisions at base station
# Note: called before a packet (or rather node) is inserted into the list
#
# conditions for collions:
#     1. same sf
#     2. frequency, see function below (Martins email, not implementet yet):
def checkcollision(packet):
    col = 0 # flag needed since there might be several collisions for packet
    processing = 0
    for i in range(0,len(packetsAtBS)):
        if packetsAtBS[i].packet.processed == 1:
            processing = processing + 1
    if (processing > maxBSReceives):
        packet.processed = 0
    else:
        packet.processed = 1

    if packetsAtBS:
        for other in packetsAtBS:
            if other.nodeid != packet.nodeid:
               # simple collision
               if frequencyCollision(packet, other.packet):
                   if sfCollision(packet, other.packet):
                       if full_collision:
                           if timingCollision(packet, other.packet):
                           # check who collides in the power domain
                               c = powerCollision(packet, other.packet)
                           # mark all the collided packets
                           # either this one, the other one, or both
                               for p in c:
                                   p.collided = 1
                           else:
                           # no timing collision, all fine
                               pass
                       else:
                           packet.collided = 1
                           other.packet.collided = 1  # other also got lost, if it wasn't lost already
                           col = 1
                   else:
                       if timingCollision(packet, other.packet):
                           if powersfCollision(packet, other.packet):
                               packet.collided = 1
                               col = 1
                       else:
                            pass                                   
        return col
    return 0

#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)):
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            return True
        #else:
    return False

def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        # p2 may have been lost too, will be marked by other checks
        return True
    return False

def powerCollision(p1, p2):
    powerThreshold = 6 # dB
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        # packets are too close to each other, both collide
        # return both packets as casualties
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        # p2 overpowered p1, return p1 as casualty
        return (p1,)
    # p2 was the weaker packet, return it as a casualty
    return (p2,)

def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        return True
    return False

# sf co-interference protection
def powersfCollision(p1, p2):
    # is SF protection enough ?
    if((p1.rssi-p2.rssi) < - interf[p1.sf-7,p2.sf-6]):
        return True
    else:
        return False    

# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload

#
# this function creates a node
#
class myNode():
    def __init__(self, nodeid, bs, period, packetlen):
        self.nodeid = nodeid
        self.period = period
        self.bs = bs
        self.x = 0
        self.y = 0

        # this is very complex prodecure for placing nodes
        # and ensure minimum distance between each pair of nodes
        global nodes
        maxDist  = Ranges_km[nodeid]
        a = random.random()
        posx = maxDist*math.cos(2*math.pi*a)+bsx
        posy = maxDist*math.sin(2*math.pi*a)+bsy
        self.x = posx
        self.y = posy
        
        # take distance from vector
        self.dist = np.sqrt((self.x-bsx)*(self.x-bsx)+(self.y-bsy)*(self.y-bsy))

        self.packet = myPacket(self.nodeid, packetlen, self.dist)
        self.sent = 0

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))

#
# this function creates a packet (associated with a node)
# it also sets all parameters, currently random
#
class myPacket():
    def __init__(self, nodeid, plen, distance):
        global experiment
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL

        self.nodeid = nodeid
        self.txpow = Ptx

        # randomize configuration values
        self.sf = random.randint(6,12)
        self.cr = random.randint(1,4)
        self.bw = random.choice([125, 250, 500])

        # for certain experiments override these
        if experiment==1 or experiment == 0:
            self.sf = 12
            self.cr = 4
            self.bw = 125

        # for certain experiments override these
        if experiment==2:
            self.sf = 6
            self.cr = 1
            self.bw = 500
        # lorawan
        if experiment == 4:
            self.sf = 12
            self.cr = 1
            self.bw = 125


        # for experiment 3 find the best setting
        # OBS, some hardcoded values
        Prx = self.txpow  ## zero path loss by default

        # log-shadow
        #Lpl = Lpld0 + 10*gamma*math.log(distance/d0)
        Lpl = Link_Loss_dB[nodeid]
        print "Lpl:", Lpl
        Prx = self.txpow - GL - Lpl

        if (experiment == 3) or (experiment == 4) or (experiment == 5):
            minairtime = 9999
            minsf = 0
            minbw = 0

            print "Prx:", Prx

            for i in range(0,6):
                for j in range(1,2):
                    if (sensi[i,j] < Prx):
                        self.sf = int(sensi[i,0])
                        if j==1:
                            self.bw = 125
                        elif j==2:
                            self.bw = 250
                        else:
                            self.bw=500
                        at = airtime(self.sf, 1, plen, self.bw)
                        if at < minairtime:
                            minairtime = at
                            minsf = self.sf
                            minbw = self.bw
                            minsensi = sensi[i, j]
            if (minairtime == 9999):
                print "does not reach base station"
                exit(-1)
            print "best sf:", minsf, " best bw: ", minbw, "best airtime:", minairtime
            self.rectime = minairtime
            self.sf = minsf
            self.bw = minbw
            self.cr = 1

            if experiment == 5:
                # reduce the txpower if there's room left
                self.txpow = max(2, self.txpow - math.floor(Prx - minsensi))
                Prx = self.txpow - GL - Lpl
                print 'minsesi {} best txpow {}'.format(minsensi, self.txpow)

        # transmission range, needs update XXX
        self.transRange = 150
        self.pl = plen
        self.symTime = (2.0**self.sf)/self.bw
        self.arriveTime = 0
        self.rssi = Prx
        # frequencies: lower bound + number of 61 Hz steps
        self.freq = 860000000 + random.randint(0,2622950)

        # for certain experiments override these and
        # choose some random frequences
        if experiment == 1:
            self.freq = random.choice([860000000, 864000000, 868000000])
        else:
            self.freq = 860000000

        print "frequency" ,self.freq, "symTime ", self.symTime
        print "bw", self.bw, "sf", self.sf, "cr", self.cr, "rssi", self.rssi
        self.rectime = airtime(self.sf,self.cr,self.pl,self.bw)
        print "rectime node ", self.nodeid, "  ", self.rectime
        # denote if packet is collided
        self.collided = 0
        self.processed = 0

#
# main discrete event loop, runs for each node
# a global list of packet being processed at the gateway
# is maintained
#
def transmit(env,node):
    while True:
        yield env.timeout(random.expovariate(1.0/float(node.period)))

        # time sending and receiving
        # packet arrives -> add to base station

        node.sent = node.sent + 1
        if (node in packetsAtBS):
            print "ERROR: packet already in"
        else:
            sensitivity = sensi[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
            if node.packet.rssi < sensitivity:
                print "node {}: packet will be lost".format(node.nodeid)
                node.packet.lost = True
            else:
                node.packet.lost = False
                # adding packet if no collision
                if (checkcollision(node.packet)==1):
                    node.packet.collided = 1
                else:
                    node.packet.collided = 0
                packetsAtBS.append(node)
                node.packet.addTime = env.now

        yield env.timeout(node.packet.rectime)

        if node.packet.lost:
            global nrLost
            nrLost += 1
        if node.packet.collided == 1:
            global nrCollisions
            nrCollisions = nrCollisions +1
        if node.packet.collided == 0 and not node.packet.lost:
            global nrReceived
            nrReceived = nrReceived + 1
        if node.packet.processed == 1:
            global nrProcessed
            nrProcessed = nrProcessed + 1

        # complete packet has been received by base station
        # can remove it
        if (node in packetsAtBS):
            packetsAtBS.remove(node)
            # reset the packet
        node.packet.collided = 0
        node.packet.processed = 0
        node.packet.lost = False

#
# "main" program
#

# get arguments
if len(sys.argv) >= 5:
    nrNodes = int(sys.argv[1])
    avgSendTime = int(sys.argv[2])
    payloadSize = int(sys.argv[3])
    experiment = int(sys.argv[4])
    simtime = int(sys.argv[5])
    if len(sys.argv) > 6:
        full_collision = bool(int(sys.argv[6]))
    print "Nodes:", nrNodes
    print "AvgSendTime (exp. distributed):",avgSendTime
    print "PayloadSize (B):",payloadSize
    print "Experiment: ", experiment
    print "Simtime: ", simtime
    print "Full Collision: ", full_collision
else:
    print "usage: ./loraSim nrNodes avgSendTime payloadSize experimentNr simtime [full_collision]"
    print "experiment 0 and 1 use 1 frequency only"
    exit(-1)


# global stuff
#Rnd = random.seed(12345)
nodes = []
packetsAtBS = []
env = simpy.Environment()

# maximum number of packets the BS can receive at the same time
maxBSReceives = 8

# packet payload size
#payloadSize = 20

# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
# also more unit-disc like according to Utz
bsId = 1
nrCollisions = 0
nrReceived = 0
nrProcessed = 0
nrLost = 0

Ptx = 13
#gamma = 2.08
gamma = 4
d0 = 40.0
var = 0           # variance ignored for now
Lpld0 = 127.41
#GL = 0
GL = -15

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])
interf = np.array([sf7d,sf8d,sf9d,sf10d,sf11d,sf12d])
if experiment in [0,1,4]:
    minsensi = sensi[5,2]  # 5th row is SF12, 2nd column is BW125
elif experiment == 2:
    minsensi = -112.0   # no experiments, so value from datasheet
elif experiment == 3:
    minsensi = np.amin(sensi) ## Experiment 3 can use any setting, so take minimum
Lpl = Ptx - minsensi
print "amin", minsensi, "Lpl", Lpl
maxDist = d0*(math.e**((Lpl-Lpld0)/(10.0*gamma)))
print "maxDist:", maxDist

# base station placement
bsx = maxDist+10
bsy = maxDist+10
xmax = bsx + maxDist + 20
ymax = bsy + maxDist + 20

# prepare graphics and add sink
if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()
    # XXX should be base station position
    ax.add_artist(plt.Circle((bsx, bsy), 3, fill=True, color='green'))
    ax.add_artist(plt.Circle((bsx, bsy), maxDist, fill=False, color='green'))


for i in range(0,nrNodes):
    # myNode takes period (in ms), base station id packetlen (in Bytes)
    # 1000000 = 16 min
    node = myNode(i,bsId, avgSendTime,payloadSize)
    nodes.append(node)
    env.process(transmit(env,node))

#prepare show
if (graphics == 1):
    plt.xlim([0, xmax])
    plt.ylim([0, ymax])
    plt.draw()
    plt.show()

# start simulation
env.run(until=simtime)

# print stats and save into file
print "nrCollisions ", nrCollisions

# compute energy
# Transmit consumption in mA from -2 to +17 dBm
TX = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
      82, 85, 90,                                          # PA_BOOST/PA1: 15..17
      105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
# mA = 90    # current draw for TX = 17 dBm
V = 3.0     # voltage XXX
sent = sum(n.sent for n in nodes)
energy = sum(node.packet.rectime * TX[int(node.packet.txpow)+2] * V * node.sent for node in nodes) / 1e6

print "energy (in J): ", energy
print "sent packets: ", sent
print "collisions: ", nrCollisions
print "received packets: ", nrReceived
print "processed packets: ", nrProcessed
print "lost packets: ", nrLost

# data extraction rate
der = (sent-nrCollisions)/float(sent)
print "DER:", der
der = (nrReceived)/float(sent)
print "DER method 2:", der

# this can be done to keep graphics visible
if (graphics == 1):
    sys.stdin.read()

# save experiment data into a dat file that can be read by e.g. gnuplot
# name of file would be:  exp0.dat for experiment 0
fname = "exp-sendtime" + str(experiment) + ".txt"
print fname
if os.path.isfile(fname):
    res = "\n" + str(avgSendTime) + "," + str(payloadSize) + "," + str(nrCollisions) + ","  + str(sent)
else:
    res = "%#simTime nrNodes TxPower\n" + str(simtime) + "," + str(nrNodes) + "," + str(Ptx) + ", 0 \n" + "%#SendTime PayloadSize nrCollisions nrTransmissions\n" + str(avgSendTime) + "," + str(payloadSize) + "," + str(nrCollisions) + ","  + str(sent)
with open(fname, "a") as myfile:
    myfile.write(res)
myfile.close()

# with open('nodes.txt','w') as nfile:
#     for n in nodes:
#         nfile.write("{} {} {}\n".format(n.x, n.y, n.nodeid))
# with open('basestation.txt', 'w') as bfile:
#     bfile.write("{} {} {}\n".format(bsx, bsy, 0))
