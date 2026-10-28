"""
AirCasta - Network & Firewall Diagnostics Module
Provides comprehensive checks for mDNS, firewall profiles, network adapters,
port availability, and router AP isolation diagnostics on Windows and macOS.
"""

import os
import platform
import socket
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DiagnosticItem:
    category: str
    name: str
    status: str  # "OK", "WARNING", "ERROR", "INFO"
    detail: str
    recommendation: str = ""


@dataclass
class DiagnosticReport:
    overall_status: str  # "OK", "WARNING", "ERROR"
    items: List[DiagnosticItem] = field(default_factory=list)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    firewall_command_fix: str = ""


class NetworkDiagnostics:
    @staticmethod
    def get_network_interfaces() -> List[Dict[str, str]]:
        interfaces = []
        try:
            # Gather local IP
            hostname = socket.gethostname()
            addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
            seen_ips = set()
            for addr in addrs:
                ip = addr[4][0]
                if ip not in seen_ips and not ip.startswith("127."):
                    seen_ips.add(ip)
                    interfaces.append({
                        "name": f"Adapter ({ip})",
                        "ip": ip,
                        "type": "IPv4"
                    })
        except Exception as e:
            interfaces.append({"name": "Error", "ip": str(e), "type": "unknown"})
        return interfaces

    @staticmethod
    def check_port_availability(port: int, proto: str = "tcp") -> bool:
        sock_type = socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM
        try:
            with socket.socket(socket.AF_INET, sock_type) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                return True
        except Exception:
            return False

    @staticmethod
    def check_windows_firewall() -> List[DiagnosticItem]:
        items = []
        if platform.system() != "Windows":
            return items

        try:
            # Check network profile (Private vs Public)
            cmd = ["powershell", "-NoProfile", "-Command", "Get-NetConnectionProfile | Select-Object -Property InterfaceAlias, NetworkCategory | ConvertTo-Json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0 and proc.stdout.strip():
                stdout = proc.stdout.strip()
                if "Public" in stdout:
                    items.append(DiagnosticItem(
                        category="Firewall",
                        name="Windows Network Profile",
                        status="WARNING",
                        detail="Текущий сетевой профиль настроен как 'Общедоступный' (Public). Windows часто блокирует mDNS-трафик и входящие подключения на публичных сетях.",
                        recommendation="Переключите профиль сети на 'Частный' (Private) в параметрах Windows -> Сеть и Интернет -> Wi-Fi."
                    ))
                else:
                    items.append(DiagnosticItem(
                        category="Firewall",
                        name="Windows Network Profile",
                        status="OK",
                        detail="Сетевой профиль частный (Private). Входящие широковещательные запросы разрешены."
                    ))
        except Exception as e:
            items.append(DiagnosticItem(
                category="Firewall",
                name="Network Profile Check",
                status="INFO",
                detail=f"Не удалось проверить сетевой профиль: {e}"
            ))

        return items

    @classmethod
    def run_full_diagnostics(cls, target_binary_path: str = "") -> DiagnosticReport:
        items = []
        overall = "OK"

        # 1. Interface check
        interfaces = cls.get_network_interfaces()
        if not interfaces:
            items.append(DiagnosticItem(
                category="Network",
                name="Локальные сетевые интерфейсы",
                status="ERROR",
                detail="Не найдено ни одного активного локального IPv4 адреса.",
                recommendation="Подключите компьютер к Wi-Fi или локальной сети Ethernet."
            ))
            overall = "ERROR"
        else:
            ip_list = ", ".join(i["ip"] for i in interfaces)
            items.append(DiagnosticItem(
                category="Network",
                name="Сетевые подключения",
                status="OK",
                detail=f"Обнаружены активные сетевые адреса: {ip_list}"
            ))

        # 2. Port checks
        ports_to_check = [
            (7000, "tcp", "RTSP AirPlay Control Port"),
            (7100, "tcp", "AirPlay Mirroring Video Port"),
            (5353, "udp", "mDNS / Bonjour Multicast Port")
        ]

        for port, proto, desc in ports_to_check:
            available = cls.check_port_availability(port, proto)
            if not available:
                # mDNS 5353 being occupied is normal if system mDNS service is active
                if port == 5353:
                    items.append(DiagnosticItem(
                        category="Ports",
                        name=f"Порт {port}/{proto.upper()} ({desc})",
                        status="INFO",
                        detail="Порт 5353 уже слушается системным сервисом Bonjour/mDNS (это нормально при совместном использовании)."
                    ))
                else:
                    items.append(DiagnosticItem(
                        category="Ports",
                        name=f"Порт {port}/{proto.upper()} ({desc})",
                        status="WARNING",
                        detail=f"Порт {port} занят другим процессом.",
                        recommendation="Убедитесь, что другое приложение AirPlay или дублирующий экземпляр не запущены."
                    ))
                    if overall != "ERROR":
                        overall = "WARNING"
            else:
                items.append(DiagnosticItem(
                    category="Ports",
                    name=f"Порт {port}/{proto.upper()} ({desc})",
                    status="OK",
                    detail=f"Порт {port} свободен и готов к приёму соединений."
                ))

        # 3. Windows Firewall checks
        firewall_items = cls.check_windows_firewall()
        items.extend(firewall_items)
        for item in firewall_items:
            if item.status == "WARNING" and overall != "ERROR":
                overall = "WARNING"

        # 4. Router AP Isolation advisory
        items.append(DiagnosticItem(
            category="Wi-Fi Router",
            name="Изоляция клиентов (AP Isolation / Client Isolation)",
            status="INFO",
            detail="В некоторых роутерах (особенно гостевых сетях Wi-Fi) включена функция 'Client Isolation', блокирующая прямую связь между iPhone и ПК.",
            recommendation="Если iPhone не видит ПК, отключите 'AP Isolation' в веб-интерфейсе вашего Wi-Fi роутера и убедитесь, что оба устройства в одной подсети."
        ))

        # Fix command for Windows firewall
        fix_cmd = ""
        if platform.system() == "Windows" and target_binary_path:
            fix_cmd = (
                f'New-NetFirewallRule -DisplayName "AirCasta AirPlay Receiver" '
                f'-Direction Inbound -Program "{target_binary_path}" -Action Allow '
                f'-Profile Any -Protocol Any'
            )

        return DiagnosticReport(
            overall_status=overall,
            items=items,
            interfaces=interfaces,
            firewall_command_fix=fix_cmd
        )
