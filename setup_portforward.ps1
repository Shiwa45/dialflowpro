# Run this script ONCE as Administrator:
#   Right-click PowerShell -> "Run as Administrator"
#   Then: cd C:\Users\easyian\dialflow && .\setup_portforward.ps1

# Forward SIP (UDP+TCP) from Windows LAN IP -> WSL2 FreeSWITCH
# OpenVox at 192.168.1.113 sends to 192.168.1.13:5070 -> FreeSWITCH at 172.31.56.241:5070

$wslIp    = "172.31.56.241"
$windowsIp = "192.168.1.13"
$sipPort   = 5070

# TCP portproxy (for SIP over TCP)
netsh interface portproxy add v4tov4 `
    listenaddress=$windowsIp listenport=$sipPort `
    connectaddress=$wslIp    connectport=$sipPort

# Windows Firewall: allow inbound on 5070 from LAN
netsh advfirewall firewall add rule `
    name="DialFlow-FreeSWITCH-SIP-5070" `
    dir=in action=allow protocol=any `
    localip=$windowsIp localport=$sipPort `
    remoteip=192.168.1.0/24

Write-Host "Port forwarding configured. Verify:"
netsh interface portproxy show all
