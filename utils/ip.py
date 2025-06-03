from fastapi import Request
from typing import Optional
import ipaddress


def get_client_ip(request: Request) -> str:

    # Check X-Forwarded-For header (most common)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first IP is usually the real client IP
        client_ip = forwarded_for.split(",")[0].strip()
        if is_valid_ip(client_ip):
            return client_ip
    
    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and is_valid_ip(real_ip):
        return real_ip
    
    # Check X-Client-IP header
    client_ip = request.headers.get("X-Client-IP")
    if client_ip and is_valid_ip(client_ip):
        return client_ip
    
    # Check CF-Connecting-IP header (Cloudflare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and is_valid_ip(cf_ip):
        return cf_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def is_valid_ip(ip_str: str) -> bool:

    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def is_private_ip(ip_str: str) -> bool:

    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False


def get_ip_info(request: Request) -> dict:
    client_ip = get_client_ip(request)
    
    return {
        "client_ip": client_ip,
        "is_valid": is_valid_ip(client_ip),
        "is_private": is_private_ip(client_ip) if is_valid_ip(client_ip) else None,
        "forwarded_for": request.headers.get("X-Forwarded-For"),
        "real_ip": request.headers.get("X-Real-IP"),
        "client_ip_header": request.headers.get("X-Client-IP"),
        "cf_connecting_ip": request.headers.get("CF-Connecting-IP"),
        "direct_client": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "host": request.headers.get("Host")
    } 