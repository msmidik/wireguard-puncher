#!/usr/bin/env python3
"""UDP hole punching server + wireguard"""
import logging
import socket
import sys
import json

BIND_HOST = '0.0.0.0'
TUNNEL_IP1 = '192.168.100.1'
TUNNEL_IP2 = '192.168.100.2'
BUFFER_SIZE = 1024 # buffer size is 1024 bytes
logger = logging.getLogger()

def create_message(peer, tunnel_ip, peer_ip):
    msg = {"ip":peer['addr'][0], "port":peer['addr'][1], "peer_ip":peer_ip, "tunnel_ip":tunnel_ip, "pubkey":peer['pubkey']}
    return json.dumps(msg).encode()

def process_registration(addr, pairing_key, pubkey, pairing_dict, sock):
    new_peer = {"addr":addr, "pubkey":pubkey}
    if pairing_key in pairing_dict:
        peers = pairing_dict.get(pairing_key)
    else:
        peers = []
    if (len(peers) == 0) or (len(peers) == 1 and peers[0]['addr'] != addr): # not same address
        peers.append(new_peer)
    if len(peers) >= 2:
        logger.info(f"sending client info to {peers[0]['addr']}")
        sock.sendto(create_message(peers[1], TUNNEL_IP1, TUNNEL_IP2), peers[0]['addr'])
        logger.info(f"sending client info to {peers[1]['addr']}")
        sock.sendto(create_message(peers[0], TUNNEL_IP2, TUNNEL_IP1), peers[1]['addr'])
        peers.pop(1)
        peers.pop(0)
    return peers

def main(port):
    pairing_dict = {}
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.bind((BIND_HOST, port))
    print(f"Server started on {BIND_HOST}:{port}")
    while True:
        raw_data, addr = sock.recvfrom(BUFFER_SIZE) 
        logger.info(f"connection from {addr} - {raw_data}")
        try: 
            data = json.loads(raw_data.decode().strip())
        except:
            continue

        if 'pairing_key' in data and 'pubkey' in data:
            pairing_key = data['pairing_key']
            pubkey = data['pubkey']
            pairing_dict[pairing_key] = process_registration(addr, pairing_key, pubkey, pairing_dict, sock)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} LISTENING_PORT")
        sys.exit(1)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main(int(sys.argv[1]))