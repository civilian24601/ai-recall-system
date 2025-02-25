# /mnt/f/projects/ai-recall-system/code_base/network_utils.py

import os

def detect_api_url(default_url="http://localhost:1234/v1/chat/completions", wsl_ip="172.17.128.1"):
    """
    Detect the correct API URL based on whether we are in WSL or native Windows.

    Args:
        default_url (str): The default local LM Studio URL to use if not in WSL.
        wsl_ip (str): The IP address to use if WSL is detected.

    Returns:
        str: The appropriate URL for LM Studio requests.
    """
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                print(f"🔹 Detected WSL! Using Windows IP: {wsl_ip}")
                return f"http://{wsl_ip}:1234/v1/chat/completions"
    except FileNotFoundError:
        pass

    print(f"🔹 Using default API URL: {default_url}")
    return default_url
