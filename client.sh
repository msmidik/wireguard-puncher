#!/bin/bash
# uses netcat-traditional, jq

LOCAL_PORT=51820
KEEPALIVE=30
PRIVKEY_FILE="privatekey"
PUBKEY_FILE="publickey"
WG_INTERFACE="wg0"

if [ "$3" == "" ]
then
    echo "usage: $0 SERVER_IP SERVER_PORT PAIRING_KEY"
    echo "remove vpn: ip link del dev $WG_INTERFACE"
    exit 0
fi

server_ip=$1
server_port=$2
pairing_key=$3

# prepare
if [ ! -e "$PRIVKEY_FILE" ]; then
    umask 077
    wg genkey > $PRIVKEY_FILE
fi
wg pubkey < $PRIVKEY_FILE > $PUBKEY_FILE
pubkey=$(cat $PUBKEY_FILE)
data="{\"pairing_key\":\"$pairing_key\", \"pubkey\":\"$pubkey\"}"

# register
echo "waiting for peer"
while true; do
    resp=$(echo "$data" | nc -u -p $LOCAL_PORT $server_ip $server_port -q 5)
    if [ -n "$resp" ]; then
        break
    fi
done
ip=$(echo "$resp" | jq -r '.ip')
port=$(echo "$resp" | jq -r '.port')
tunnel_ip=$(echo "$resp" | jq -r '.tunnel_ip')
peer_ip=$(echo "$resp" | jq -r '.peer_ip')
peer_pubkey=$(echo "$resp" | jq -r '.pubkey')
echo "0" | nc -u -p $LOCAL_PORT $ip $port -q 0.1 > /dev/null

# create vpn
echo 'creating VPN'
ip link add dev $WG_INTERFACE type wireguard
ip address add dev $WG_INTERFACE $tunnel_ip/30
wg set $WG_INTERFACE private-key $PRIVKEY_FILE listen-port $LOCAL_PORT peer $peer_pubkey allowed-ips $peer_ip/32 endpoint $ip:$port persistent-keepalive $KEEPALIVE
ip link set up dev $WG_INTERFACE
echo "VPN created, peer has ip address $peer_ip"