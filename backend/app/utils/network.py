import socket

def is_network_available(timeout: float = 0.5) -> bool:
    """
    Checks whether external internet is accessible in <0.5 seconds without blocking.
    Tests standard HTTPS endpoints (port 443) to avoid firewall restrictions on port 53.
    """
    targets = [("1.1.1.1", 443), ("8.8.8.8", 443), ("8.8.8.8", 53)]
    for host, port in targets:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            res = s.connect_ex((host, port))
            s.close()
            if res == 0:
                return True
        except Exception:
            continue
    return False


