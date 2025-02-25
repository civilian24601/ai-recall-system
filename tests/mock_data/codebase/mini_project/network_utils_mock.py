"""
network_utils_mock.py
A minimal mock for detecting environment or returning a default URL.
No external deps required.
"""

def detect_api_url(default_url="http://localhost:9999", wsl_ip="172.17.128.1"):
    """
    Mock version of environment detection.
    Always returns the default for this mini-project.
    """
    return default_url

def ping_remote_service(url):
    """
    Mock ping to a remote service—always returns True.
    """
    print(f"Pretending to ping {url}")
    return True
