[![Build Status](https://secure.travis-ci.org/iffy/ppo.png?branch=master)](http://travis-ci.org/iffy/ppo)

`ppo` parses output from commands that don't have nicely parsed output.  Here's a picture:


    whatever output the program gives -> ppo -> YAML/JSON/XML

# Example #

For instance, here's parsing `nmap` xml output:

    nmap -sP 192.168.13.205 -oX - | ppo

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

Nmap already has pretty nice output.  `ppo` was made for other programs that have garbage output.


# Supported programs #

See a list of parseable formats with `ppo --ls`.

