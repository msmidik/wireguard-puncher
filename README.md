# Wireguard - UDP hole punching

Simple scripts for establish VPN connection between devices that are both behind NAT. It needs server with public IP address to establish connection using [UDP hole punching](https://en.wikipedia.org/wiki/UDP_hole_punching).

## Client scripts

- for Windows (PowerShell), for Linux (Python, Bash)
- requires wireguard installed

## Server script

- in Python

## Establishing a connection (protocol)

- client sends to the UDP port of the server: {"pairing_key":*pairing_key*, "pubkey":*pubkey*}
- when server gets same pairing_key from two clients, it sends them: {"ip":*peer_nat_ip*, "port":*peer_nat_port*, "peer_ip":*peer_vpn_ip*, "tunnel_ip":*my_tunnel_ip*, "pubkey":*peer_pubkey*}
- with this both clients can create a direct UDP connection

## TODO

- renegotiate connection when connection is down and NAT changes port
- use some database for keeping pairing_keys on the server
- encrypting communication with the server - in theory attacker could eavesdrop the pairing_key of the first client and use it for establishing connection