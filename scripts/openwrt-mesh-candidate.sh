#!/bin/sh
# i™ OpenWrt 802.11s + batman-adv candidate configuration generator.
# NEVER applies changes. Run on a supported OpenWrt router after inspecting
# backup configs and confirming physical 802.11s radio driver support.
set -eu
[ "${1:-}" = "--dry-run" ] || { echo "Usage: sh openwrt-mesh-candidate.sh --dry-run [mesh-id]" >&2; exit 2; }
MESH_ID="${2:-i-community-lab}"
case "$MESH_ID" in *[!a-zA-Z0-9_-]*|"") echo "Unsafe mesh ID" >&2; exit 2;; esac
[ "${#MESH_ID}" -le 32 ] || { echo "Mesh ID too long" >&2; exit 2; }
cat <<EOF
# CANDIDATE ONLY — NOT INSTALLED.
# Before applying on isolated test hardware:
# 1) save /etc/config/wireless, /etc/config/network, firewall
# 2) check iw phy supports mesh point and channel availability
# 3) install firmware-matched batman-adv, batctl and mesh-capable wpad
# 4) provision a per-network SAE passphrase out of band
# 5) do not bridge this segment to wan/lan or open a public exit
# Tested radio interface and channel selection required.
uci set network.bat0='interface'
uci set network.bat0.proto='batadv'
uci set network.bat0.routing_algo='BATMAN_IV'
uci set network.bat0.aggregated_ogms='1'
uci set network.mesh0='interface'
uci set network.mesh0.proto='batadv_hardif'
uci set network.mesh0.master='bat0'
uci set wireless.imesh='wifi-iface'
uci set wireless.imesh.device='<RADIO_NAME_REPLACE>'
uci set wireless.imesh.mode='mesh'
uci set wireless.imesh.mesh_id='$MESH_ID'
uci set wireless.imesh.encryption='sae'
uci set wireless.imesh.key='<REPLACE_WITH_STRONG_UNIQUE_KEY>'
uci set wireless.imesh.network='mesh0'
# No uci commit/reload is executed by this script.
# Keep a management path independent of experimental mesh backhaul.
EOF
