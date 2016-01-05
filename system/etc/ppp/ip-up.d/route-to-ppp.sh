#!/bin/bash

IFACE="ppp0"

NET=$(ifconfig $IFACE | egrep -o "inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | cut -d" " -f2 | cut -d"." -f1-3).0
route add -net ${NET} dev ${IFACE}
