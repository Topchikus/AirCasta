"""
AirCasta - Python Zeroconf AirPlay Advertiser
Provides dual-layer mDNS broadcasting on the physical LAN adapter (192.168.x.x)
to ensure iOS devices immediately discover the receiver without interference
from VPNs, virtual adapters, or Windows firewall quirks.
"""

import socket
from typing import Optional
from zeroconf import IPVersion, ServiceInfo, Zeroconf


class AirPlayBroadcaster:
    def __init__(self, name: str, ip: str, mac_str: str, port: int = 7000):
        self.name = name
        self.ip = ip
        # Format MAC: uppercase without colons for RAOP, lowercase with colons for AirPlay
        raw_mac = mac_str.replace(":", "").replace("-", "").lower()
        self.mac_upper_raw = raw_mac.upper()
        if len(raw_mac) == 12:
            self.mac_colon = ":".join(raw_mac[i:i+2] for i in range(0, 12, 2))
        else:
            self.mac_colon = mac_str.lower()

        self.port = port
        self.zeroconf: Optional[Zeroconf] = None
        self.airplay_info: Optional[ServiceInfo] = None
        self.raop_info: Optional[ServiceInfo] = None

    def start(self):
        try:
            # Bind specifically to the physical IP interface to avoid VPN / Clash tunnel routing
            try:
                self.zeroconf = Zeroconf(interfaces=[self.ip], ip_version=IPVersion.V4Only)
            except Exception:
                self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)

            ip_bytes = socket.inet_aton(self.ip)

            # 1. Register _airplay._tcp.local.
            # Apple AirPlay specification: deviceid must be lowercase with colons
            airplay_props = {
                b"deviceid": self.mac_colon.encode("utf-8"),
                b"features": b"0x5A7FFEE6,0x0",
                b"flags": b"0x4",
                b"model": b"AppleTV3,2",
                b"pk": b"b07727d6f6cd6e08b58ede525ec3cdeaa252ad9f683feb212ef8a205246554e7",
                b"pi": b"2e388006-13ba-4041-9a67-25dd4a43d536",
                b"srcvers": b"220.68",
                b"vv": b"2",
                b"pw": b"false"
            }

            self.airplay_info = ServiceInfo(
                type_="_airplay._tcp.local.",
                name=f"{self.name}._airplay._tcp.local.",
                addresses=[ip_bytes],
                port=self.port,
                properties=airplay_props,
                server=f"AirCasta-{self.mac_upper_raw}.local."
            )
            self.zeroconf.register_service(self.airplay_info)

            # 2. Register _raop._tcp.local.
            # RAOP service name: <UPPERCASE_MAC_NO_COLONS>@<NAME>._raop._tcp.local.
            raop_props = {
                b"ch": b"2",
                b"cn": b"0,1,2,3",
                b"da": b"true",
                b"et": b"0,3,5",
                b"vv": b"2",
                b"ft": b"0x5A7FFEE6,0x0",
                b"am": b"AppleTV3,2",
                b"md": b"0,1,2",
                b"rhd": b"5.6.0.0",
                b"pw": b"false",
                b"sr": b"44100",
                b"ss": b"16",
                b"sv": b"false",
                b"tp": b"UDP",
                b"txtvers": b"1",
                b"vs": b"220.68",
                b"vn": b"65537",
                b"sf": b"0x4",
                b"pk": b"b07727d6f6cd6e08b58ede525ec3cdeaa252ad9f683feb212ef8a205246554e7"
            }

            self.raop_info = ServiceInfo(
                type_="_raop._tcp.local.",
                name=f"{self.mac_upper_raw}@{self.name}._raop._tcp.local.",
                addresses=[ip_bytes],
                port=self.port,
                properties=raop_props,
                server=f"AirCasta-{self.mac_upper_raw}.local."
            )
            self.zeroconf.register_service(self.raop_info)
            print(f"[Zeroconf] AirPlay advertised on {self.ip}:{self.port} as '{self.name}' (MAC {self.mac_colon})")

        except Exception as e:
            print(f"[Zeroconf] Failed to broadcast AirPlay: {e}")

    def stop(self):
        if self.zeroconf:
            try:
                if self.airplay_info:
                    self.zeroconf.unregister_service(self.airplay_info)
                if self.raop_info:
                    self.zeroconf.unregister_service(self.raop_info)
                self.zeroconf.close()
            except Exception:
                pass
            self.zeroconf = None
