[![Build Status](https://secure.travis-ci.org/iffy/ppo.png?branch=master)](http://travis-ci.org/iffy/ppo)

`ppo` parses output from commands that don't have nicely parsed output.  Here's a picture:


    whatever output the program gives -> ppo -> YAML/JSON

# Installation #

Install the latest stable release from PyPi:

    pip install ppo

Or install the most recent stable, unreleased version from GitHub:

    pip install git+https://github.com/iffy/ppo.git

# Example #

For instance, here's parsing `nmap` xml output:

    nmap -sP 192.168.13.205 -oX - | ppo -f yaml

Which produces:

```yml
hosts:
- addresses:
  - addr: 192.168.13.205
    addrtype: ipv4
  hostnames: []
  status:
    reason: reset
    reason_ttl: 255
    state: up
  times:
    rttvar: 5000
    srtt: 123
    to: 100000
nmaprun:
  args: nmap -sP -oX - 192.168.13.205
  debugging:
    level: 0
  runstats:
    finished:
      elapsed: 0.02
      exit: success
      summary: Nmap done at Thu Aug 27 17:19:29 2015; 1 IP address (1 host up) scanned
        in 0.02 seconds
      time: 1440710369
      timestr: Thu Aug 27 17:19:29 2015
    hosts:
      down: 0
      total: 1
      up: 1
  scanner: nmap
  start: 1440710369
  startstr: Thu Aug 27 17:19:29 2015
  verbose:
    level: 0
  version: '6.47'
  xmloutputversion: '1.04'
```

And here's `iptables -L`:

    iptables -nvL | ppo -f yaml

```yml
INPUT:
  ACCEPT:
    packets: "3930"
    bytes: "449K"
  items:
    - pkts: "0"
      bytes: "0"
      target: ACCEPT
      prot: all
      opt: --
      in: "*"
      out: "*"
      source: 192.168.1.205
      destination: 0.0.0.0/0
    - pkts: "3113"
      bytes: "128K"
      target: ACCEPT
      prot: all
      opt: --
      in: "*"
      out: "*"
      source: 192.168.13.206
      destination: 0.0.0.0/0
FORWARD:
  ACCEPT:
    packets: "0"
    bytes: "0"
  items: []
OUTPUT:
  ACCEPT:
    packets: "4352"
    bytes: "523K"
  items:
    - pkts: "4074"
      bytes: "183K"
      target: ACCEPT
      prot: all
      opt: --
      in: "*"
      out: "*"
      source: 0.0.0.0/0
      destination: 192.168.13.206
```

## Use it with jq ##

By default, `ppo` renders JSON, making it nice to use with [jq](https://stedolan.github.io/jq/):

    # iptables -nvL | ppo | jq '.INPUT.items[] | select(.source == "192.168.1.205")'
    {
      "opt": "--",
      "destination": "0.0.0.0/0",
      "target": "ACCEPT",
      "prot": "all",
      "bytes": "0",
      "source": "192.168.1.205",
      "in": "*",
      "pkts": "0",
      "out": "*"
    }


## Use it with grep ##

You can produce greppable/cuttable output with `-f grep`:

    $ cat functests/cases/in-nmap-1 | ppo -f grep | grep 'port: 443'
    hosts: endtime: 1440623310 hostnames: [] ipv4: 192.168.13.203 starttime: 1440623308 ports: port: 443 protocol: tcp
    hosts: endtime: 1440623310 hostnames: [] ipv4: 192.168.13.203 starttime: 1440623308 ports: port: 443 protocol: tcp service: conf: 3 method: table name: https
    hosts: endtime: 1440623310 hostnames: [] ipv4: 192.168.13.203 starttime: 1440623308 ports: port: 443 protocol: tcp state: reason: no-response reason_ttl: 0 state: filtered

Or this:

    $ cat functests/cases/in-nmap-1 | ppo -f grep | grep 'state: open'
    hosts: endtime: 1440623310 hostnames: [] ipv4: 192.168.13.203 starttime: 1440623308 ports: port: 80 protocol: tcp state: reason: syn-ack reason_ttl: 128 state: open

# Supported programs #

See a list of parseable formats with `ppo --ls` or look in [ppo/parse_plugins](ppo/parse_plugins/).

