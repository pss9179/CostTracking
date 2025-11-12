"""
Proxy manager for auto-starting local proxy server.

OPTIONAL: Only needed if user wants auto_start_proxy=True.
"""
import subprocess
import time
import logging

logger = logging.getLogger("llmobserve")


def start_local_proxy(port: int = 9000, collector_url: str = "http://localhost:8000") -> str:
    """
    Start local proxy server as background process.
    
    Args:
        port: Port to run proxy on (default: 9000)
        collector_url: URL of the collector (passed to proxy)
    
    Returns:
        Proxy URL (e.g., "http://localhost:9000")
    
    Raises:
        RuntimeError: If proxy fails to start
    """
    import os
    
    # Set collector URL env var for proxy
    env = os.environ.copy()
    env["LLMOBSERVE_COLLECTOR_URL"] = collector_url
    
    # Start proxy as subprocess
    try:
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "proxy.main:app", "--host", "0.0.0.0", "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
        
        # Wait for proxy to start
        proxy_url = f"http://localhost:{port}"
        
        for i in range(30):  # 3 second timeout
            try:
                import requests
                response = requests.get(f"{proxy_url}/health", timeout=0.1)
                if response.status_code == 200:
                    logger.info(f"[llmobserve] Proxy started successfully on {proxy_url}")
                    return proxy_url
            except:
                time.sleep(0.1)
        
        # Timeout
        process.terminate()
        raise RuntimeError("[llmobserve] Proxy failed to start within 3 seconds")
    
    except Exception as e:
        logger.error(f"[llmobserve] Failed to start proxy: {e}")
        raise RuntimeError(f"Failed to start proxy: {e}")

