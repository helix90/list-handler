#!/usr/bin/env python3
"""Simple healthcheck script for Docker"""
import urllib.request
import sys
import socket

def check_health():
    """Check if the health endpoint is responding"""
    try:
        # First check if port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8088))
        sock.close()
        
        if result != 0:
            return False
        
        # Then check the health endpoint
        response = urllib.request.urlopen('http://localhost:8088/health', timeout=3)
        if response.getcode() == 200:
            return True
        return False
    except Exception as e:
        return False

if __name__ == '__main__':
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)

