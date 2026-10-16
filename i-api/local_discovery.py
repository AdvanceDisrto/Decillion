"""i™ Local Discovery Native Bridge — opt-in, read-only probes.

Run on a trusted desktop / edge host, not on the public Render instance.
No automatically trusted peers and no remote executable commands.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import platform
import shutil
import socket
import subprocess
import time

def local_interfaces():
    """Socket bind probe verifies only that local TCP/UDP networking works."""
    results={}
    for mode,socktype in (("tcp",socket.SOCK_STREAM),("udp",socket.SOCK_DGRAM)):
        s=socket.socket(socket.AF_INET,socktype)
        try:
            s.bind(("127.0.0.1",0))
            if mode=="tcp":s.listen(1)
            results[mode]={"loopback_socket_open":True,"local_port":s.getsockname()[1]}
        except OSError as exc:
            results[mode]={"loopback_socket_open":False,"reason":type(exc).__name__}
        finally:s.close()
    return results

async def scan_ble(seconds=3):
    """An actual OS BLE scan, never claiming a connection or pairing."""
    try:
        from bleak import BleakScanner
    except ImportError:
        return {"supported":False,"scan_performed":False,
                "reason":"Install bleak on a native host; browser/Render cannot run this scan."}
    try:
        found=await BleakScanner.discover(timeout=min(max(seconds,1),8))
        return {"supported":True,"scan_performed":True,
                "observed_count":len(found),
                "devices":[{"name":str(d.name or ""),"address":str(d.address)} for d in found[:25]],
                "paired":False,"authenticated":False}
    except Exception as exc:
        return {"supported":False,"scan_performed":False,
                "reason":type(exc).__name__+": "+str(exc)[:200]}

def wifi_direct():
    """Real OS capability information; not a Wi-Fi Direct peer/session handshake."""
    system=platform.system()
    if system=="Windows":
        command=["netsh","wlan","show","drivers"]
    elif system=="Linux" and shutil.which("iw"):
        command=["iw","list"]
    else:
        return {"os":system,"capability_checked":False,"session_active":False,
                "reason":"Platform-specific Wi-Fi Direct SDK/permissions required"}
    try:
        p=subprocess.run(command,capture_output=True,text=True,timeout=9,check=False)
        observed=p.returncode==0
        return {"os":system,"capability_checked":observed,
                "session_active":False,"peer_discovered":False,
                "hint":"Inspect native driver output separately; not proof of P2P support",
                "driver_output_excerpt":p.stdout[:1800] if observed else p.stderr[:250]}
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"os":system,"capability_checked":False,"session_active":False,"reason":type(exc).__name__}

def discover_lan(seconds=3):
    """Actual mDNS service discovery when zeroconf is installed.

    Never automatically joins a discovered service; discovery isn't authentication.
    """
    try:
        from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
    except ImportError:
        return {"discovery_performed":False,"peer_authenticated":False,
                "reason":"Install zeroconf on native host to scan mDNS"}
    observed=[]
    class Listener(ServiceListener):
        def add_service(self,z,type_,name):
            observed.append({"service":name,"service_type":type_})
        def update_service(self,z,type_,name):pass
        def remove_service(self,z,type_,name):pass
    z=Zeroconf()
    try:
        browser=ServiceBrowser(z,["_http._tcp.local.","_iuniversalapi._tcp.local."],Listener())
        time.sleep(min(max(seconds,1),8))
        browser.cancel()
        return {"discovery_performed":True,"peer_authenticated":False,
                "services":observed[:50],"service_count":len(observed)}
    except Exception as exc:
        return {"discovery_performed":False,"peer_authenticated":False,
                "reason":type(exc).__name__}
    finally:z.close()

async def report(ble=False,lan=False,wifi=False,seconds=3):
    return {"schema":"i-local-discovery/1","os":platform.platform(),
            "mode":"native-local-host-only",
            "socket_test":local_interfaces(),
            "bluetooth":await scan_ble(seconds) if ble else {"scan_performed":False,"enabled":False},
            "wifi_direct":wifi_direct() if wifi else {"capability_checked":False,"enabled":False},
            "lan":discover_lan(seconds) if lan else {"discovery_performed":False,"enabled":False},
            "p2p_authenticated":False,"encrypted_session_established":False,
            "witness":"locally_observed;not_certified"}

def main():
    p=argparse.ArgumentParser(description="i™ native opt-in BLE/LAN/Wi-Fi driver capability diagnostics")
    p.add_argument("--ble",action="store_true",help="Scan nearby BLE advertisements")
    p.add_argument("--lan",action="store_true",help="Scan local mDNS; requires zeroconf")
    p.add_argument("--wifi",action="store_true",help="Read OS Wi-Fi capability; no P2P session")
    p.add_argument("--seconds",type=int,default=3,choices=range(1,9))
    args=p.parse_args()
    print(json.dumps(asyncio.run(report(args.ble,args.lan,args.wifi,args.seconds)),indent=2))

if __name__=="__main__":main()
