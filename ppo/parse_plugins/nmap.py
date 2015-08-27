from ppo import plugins

from lxml import etree

def mapType(data, mapping):
    """
    Map values in `data` dict to those described in `mapping` dict
    """
    ret = {}
    for key in data:
        t = mapping.get(key)
        if t:
            ret[key] = t(data[key])
        else:
            ret[key] = data[key]
    return ret


class NmapXMLParser(plugins.ParserPlugin):
    """
    I parse Nmap XML output
    """

    name = 'nmap-xml'

    def readProbability(self, instream):
        first_part = instream.read(200)
        if 'nmap' in first_part and 'xml' in first_part:
            return 50

    def parse(self, instream):
        xml = etree.parse(instream)
        root = xml.getroot()

        results = {}

        nmaprun = results['nmaprun'] = {}
        nmaprun.update(mapType(root.attrib, {
            'start': int,
        }))

        hosts = results['hosts'] = []
        
        for child in root:
            if child.tag == 'host':
                hosts.append(self._parseHost(child))
            elif child.tag == 'runstats':
                nmaprun['runstats'] = runstats = dict(child.attrib)
                for stat in child:
                    mapping = {
                        'finished': {
                            'elapsed': float,
                            'time': int,
                        },
                        'hosts': {
                            'down': int,
                            'total': int,
                            'up': int,
                        }
                    }.get(stat.tag, {})
                    runstats[stat.tag] = self._parseNode(stat, mapping)
            else:
                mapping = {
                    'scaninfo': {
                        'numservices': int,
                    },
                    'verbose': {
                        'level': int,
                    },
                    'debugging': {
                        'level': int,
                    },
                }.get(child.tag, {})
                nmaprun[child.tag] = self._parseNode(child, mapping)
        return results

    def _parseHost(self, host):
        ret = mapType(host.attrib, {
            'endtime': int,
            'starttime': int,
        })
        ret.update({
            'addresses': [],
        })

        for tag in host:
            if tag.tag == 'address':
                ret['addresses'].append(self._parseNode(tag))
            elif tag.tag == 'ports':
                ret['ports'] = [self._parsePort(x) for x in tag]
            elif tag.tag == 'hostnames':
                ret['hostnames'] = []
            elif tag.tag == 'hostscript':
                if 'hostscripts' not in ret:
                    ret['hostscripts'] = []
                ret['hostscripts'].append(self._parseHostScripts(tag))
            else:
                mapping = {
                    'status': {
                        'reason_ttl': int,
                    },
                    'times': {
                        'rttvar': int,
                        'srtt': int,
                        'to': int,
                    }
                }.get(tag.tag, {})
                ret[tag.tag] = self._parseNode(tag, mapping)
        return ret

    def _parsePort(self, port):
        ret = dict(port.attrib)
        ret['port'] = int(ret.pop('portid'))
        for child in port:
            mapping = {
                'service': {
                    'conf': int,
                },
                'state': {
                    'reason_ttl': int,
                }
            }.get(child.tag, {})
            ret[child.tag] = self._parseNode(child, mapping)
        return ret

    def _parseHostScripts(self, xml):
        script = xml.find('.//script')
        ret = dict(script.attrib)
        data = ret['data'] = {}
        for elem in script:
            data[elem.attrib['key']] = elem.text
        return ret


    def _parseNode(self, node, mapping=None):
        mapping = mapping or {}
        ret = mapType(node.attrib, mapping)
        children = []
        for child in node:
            children.append(self._parseNode(child))
        if children:
            ret['children'] = children
        return ret


