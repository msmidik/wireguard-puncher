$DEFAULT_PORT = 51820
$PRIVKEY_FILE = 'privatekey'
$PUBKEY_FILE = 'publickey'
$WG_INTERFACE = 'wg0'
$WG_CONF = "$WG_INTERFACE.conf"
$KEEPALIVE = 30


function prepare($pairingKey) {
    if (-not (Test-Path $PRIVKEY_FILE)) {
        wg genkey > $PRIVKEY_FILE
    }
    $pubkey = Get-Content $PRIVKEY_FILE | wg pubkey
    $pubkey > $PUBKEY_FILE
    return "{`"pairing_key`":`"$pairingKey`", `"pubkey`":`"$pubkey`"}"
}

function register($socketPort, $serverIp, $serverPort, $msg) {
    Write-Output 'waiting for peer'
    $udpClient = new-Object System.Net.Sockets.UdpClient $socketPort
    $msgData = [Text.Encoding]::ascii.GetBytes($msg)
    [void] $udpClient.Send($msgData, $msgData.length, $serverIP, $serverPort)

    $endpoint = new-object System.Net.IPEndPoint ([IPAddress]::Any, 0)
    $respData = $udpclient.Receive([ref]$endpoint)
    $resp = ConvertFrom-Json ([Text.Encoding]::ASCII.GetString($respData))

    [void] $udpClient.Send(0, 1, $resp.ip, $resp.port)

    $udpClient.close()
    return $resp
}

function createVpn($socketPort, $data) {
    Write-Output 'creating VPN'

    "[Interface]" > $WG_CONF
    "PrivateKey = $(Get-Content $PRIVKEY_FILE)" >> $WG_CONF
    "Address = $($data.tunnel_ip)/30" >> $WG_CONF
    "ListenPort = $socketPort"  >> $WG_CONF
    "[Peer]" >> $WG_CONF
    "PublicKey = $($data.pubkey)"  >> $WG_CONF
    "Endpoint = $($data.ip):$($data.port)" >> $WG_CONF
    "AllowedIPs = $($data.peer_ip)/32" >> $WG_CONF
    "PersistentKeepalive = $KEEPALIVE" >> $WG_CONF

    $confPath = Get-ChildItem $WG_CONF | Select-Object -ExpandProperty FullName
    wireguard /installtunnelservice $confPath
    Write-Output "VPN created, peer has ip address $($data.peer_ip)"
}

function main ($serverIp, $serverPort, $pairingKey, $socketPort) {
    $msg = prepare $pairingKey
    $data = register $socketPort $serverIp $serverPort $msg
    createVpn $socketPort $data
}


if ($args.Count -lt 3) {
    Write-Output "Usage: SERVER_IP SERVER_PORT PAIRING_KEY [SOCKET_PORT default $DEFAULT_PORT]"
    Write-Output "remove vpn: wireguard /uninstalltunnelservice $WG_INTERFACE"
} elseif ($args.Count -eq 3) {
    main $args[0] $args[1] $args[2] $DEFAULT_PORT
} else {
     main $args[0] $args[1] $args[2] $args[3]
}