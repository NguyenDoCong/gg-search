import os
import subprocess
import time
import requests
from pathlib import Path
from stem.control import Controller
from stem import Signal

NUM_INSTANCES = 40
BASE_PORT = 9050
BASE_DIR = Path.home() / "multi_tor"
TOR_BIN = "tor"
TOR_READY_MSG = "Bootstrapped 100%"

def create_torrc_instances():
    BASE_DIR.mkdir(exist_ok=True)
    for i in range(NUM_INSTANCES):
        socks_port = BASE_PORT + i * 2
        control_port = socks_port + 1
        instance_dir = BASE_DIR / f"tor{i}"
        data_dir = instance_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        torrc_path = instance_dir / "torrc"
        torrc_content = f"""SocksPort {socks_port}
        ControlPort {control_port}
        DataDirectory {data_dir}
        CookieAuthentication 1
        CookieAuthFileGroupReadable 1
        """

        torrc_path.write_text(torrc_content, encoding="utf-8")
        print(f"✅ Created torrc {torrc_path}")

def run_tor_instances():
    processes = []
    for i in range(NUM_INSTANCES):
        torrc_path = BASE_DIR / f"tor{i}/torrc"
        log_path = BASE_DIR / f"tor{i}/output.log"
        log_file = open(log_path, "w")
        proc = subprocess.Popen(
            [TOR_BIN, "-f", str(torrc_path)],
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        processes.append((proc, log_path))
        print(f"🚀 Started Tor instance {i}")
    return processes

def wait_until_bootstrapped(log_paths, timeout=60):
    print("⏳ Waiting for Tor circuits to bootstrap...")

    start_time = time.time()
    ready_flags = [False] * NUM_INSTANCES

    while not all(ready_flags):
        for i, log_path in enumerate(log_paths):
            if ready_flags[i]:
                continue  # skip already ready
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if TOR_READY_MSG in content:
                        print(f"✅ Instance {i} bootstrapped.")
                        ready_flags[i] = True
            except Exception:
                pass

        if time.time() - start_time > timeout:
            print("❌ Timeout waiting for Tor to bootstrap.")
            break

        # time.sleep(1)

def send_newnym(control_port):
    try:
        with Controller.from_port(port=control_port) as controller:
            controller.authenticate()  # dùng cookie authentication
            controller.signal(Signal.NEWNYM)
            print(f"🔄 Sent NEWNYM to control port {control_port}")
    except Exception as e:
        print(f"❌ Failed to send NEWNYM on port {control_port}: {e}")

async def test_tor_instance(i):
    # print("🌐 Checking IP addresses for each instance:")
    # for i in range(NUM_INSTANCES):
        port = BASE_PORT + i * 2
        control_port = port + 1

        send_newnym(control_port)  # gửi NEWNYM trước khi test

        proxies = {
            "http": f"socks5h://127.0.0.1:{port}",
            "https": f"socks5h://127.0.0.1:{port}"
        }
        try:
            # time.sleep(5)  # đợi IP mới được áp dụng
            resp = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            ip = resp.json().get("ip", "unknown")
            print(f"[Instance {i}] 🧅 IP: {ip}")
        except Exception as e:
            print(f"[Instance {i}] ❌ Error: {e}")

def cleanup(processes):
    print("🛑 Stopping all Tor processes...")
    for proc, _ in processes:
        proc.terminate()
    print("✅ All processes terminated.")

if __name__ == "__main__":
    import asyncio
    
    async def main_test():
    
        create_torrc_instances()
        processes = run_tor_instances()
        log_paths = [log for _, log in processes]

        try:
            wait_until_bootstrapped(log_paths)
            tasks = [test_tor_instance(i) for i in range(NUM_INSTANCES)]

            await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            # cleanup(processes)
            pass
            
    asyncio.run(main_test())
            
