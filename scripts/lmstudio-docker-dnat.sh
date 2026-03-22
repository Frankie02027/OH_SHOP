#!/bin/bash
# Forward Docker container traffic for port 1234 to localhost (LM Studio).
# The DNAT rule alone is not enough: the Docker ingress bridge also needs
# route_localnet enabled so bridged packets may be forwarded to 127.0.0.1.
# Host firewall policy for Docker-subnet traffic to tcp/1234 should be managed
# separately by UFW or the host firewall, not by this helper.
#
# Run at boot or after Docker restarts:
#   sudo /home/dev/OH_SHOP/scripts/lmstudio-docker-dnat.sh
set -euo pipefail

for path in \
  /proc/sys/net/ipv4/conf/all/route_localnet \
  /proc/sys/net/ipv4/conf/default/route_localnet; do
  echo 1 >"$path"
done

for path in /proc/sys/net/ipv4/conf/docker0/route_localnet /proc/sys/net/ipv4/conf/br-*/route_localnet; do
  if [ -e "$path" ]; then
    echo 1 >"$path"
  fi
done

iptables -t nat -C PREROUTING -p tcp -s 172.16.0.0/12 --dport 1234 -j DNAT --to-destination 127.0.0.1:1234 2>/dev/null || \
iptables -t nat -I PREROUTING -p tcp -s 172.16.0.0/12 --dport 1234 -j DNAT --to-destination 127.0.0.1:1234

echo "LM Studio Docker forwarding active (172.16.0.0/12:1234 -> 127.0.0.1:1234)"
