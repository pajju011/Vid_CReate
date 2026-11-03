import socket

def is_network_available(timeout: float = 0.4) -> bool:
    """
    Checks whether external internet is accessible in <0.4 seconds without blocking.
    Allows instant local fallback when offline or in sandbox.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex(("1.1.1.1", 53))
        s.close()
        return result == 0
    except Exception:
        return False

