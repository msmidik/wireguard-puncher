#!/usr/bin/env python3
"""UDP hole punching client + wireguard
requires python 3 and wiregurd installed"""
import socket
import sys
import json
import subprocess

BIND_HOST = '0.0.0.0'
DEFAULT_PORT = 51820
TIMEOUT = 30
PRIVKEY_FILE = 'privatekey'
PUBKEY_FILE = 'publickey'
BUFFER_SIZE = 1024
WG_INTERFACE = 'wg0'

def run_shell(cmd):
    subprocess.run(cmd, shell=True)

def run_secure(cmd):
    subprocess.run(cmd.split())

def run_secure_output(cmd):
    return subprocess.check_output(cmd.split()).decode().strip()
    
def prepare(pairing_key):
    run_shell(f'umask 077; if [ ! -f {PRIVKEY_FILE} ]; then wg genkey > {PRIVKEY_FILE} ; fi')
    run_shell(f'wg pubkey < {PRIVKEY_FILE} > {PUBKEY_FILE}')
    pubkey = run_secure_output(f'cat {PUBKEY_FILE}')
    msg_dict = {"pairing_key":pairing_key, "pubkey":pubkey}
    return json.dumps(msg_dict).encode()

def register(sock, server_ip, server_port, msg):
    print('waiting for peer')
    while True:
        sock.sendto(msg, (server_ip, server_port))
        try:
            raw_data, addr = sock.recvfrom(BUFFER_SIZE)
            print(f'received from {addr} - {raw_data}')
            data = json.loads(raw_data.decode().strip())
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            continue
        sock.sendto(b'0', (data['ip'], data['port']))
        break
    return data

def create_vpn(socket_port, data):
    print('creating VPN')
    run_secure(f'ip link add dev {WG_INTERFACE} type wireguard')
    run_secure(f'ip address add dev {WG_INTERFACE} {data["tunnel_ip"]}/30')
    run_secure(f'wg set {WG_INTERFACE} private-key {PRIVKEY_FILE} listen-port {socket_port} peer {data["pubkey"]} allowed-ips {data["peer_ip"]}/32 endpoint {data["ip"]}:{data["port"]} persistent-keepalive {TIMEOUT}')
    run_secure(f'ip link set up dev {WG_INTERFACE}')
    print(f'VPN created, peer has ip address {data["peer_ip"]}')

def main(server_ip, server_port, pairing_key, socket_port=DEFAULT_PORT):
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.bind((BIND_HOST, socket_port))
    sock.settimeout(TIMEOUT)
    msg = prepare(pairing_key)
    data = register(sock, server_ip, server_port, msg)
    sock.close()
    create_vpn(socket_port, data)
    
    
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} SERVER_IP SERVER_PORT PAIRING_KEY [SOCKET_PORT default {DEFAULT_PORT}]\n\
        remove vpn: ip link del dev {WG_INTERFACE}")
        sys.exit(1)
    elif len(sys.argv) == 4:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))