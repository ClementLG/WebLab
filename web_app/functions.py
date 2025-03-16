import socket
import re


def is_valid_hostname(hostname):
    """
    Validates a hostname.

    A basic check, you might need to make it more robust 
    depending on your specific requirements.
    """
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip trailing dot
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def is_valid_ipv4_address(ip):
    """Validates an IPv4 address."""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

def is_valid_ipv6_address(ip):
    """
    Validates an IPv6 address.
    This is a basic check and might not cover all IPv6 complexities.
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False