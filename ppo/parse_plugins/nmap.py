from ppo import plugins

from lxml import etree


class NmapXMLParser(plugins.ParserPlugin):
    """
    I parse Nmap XML output
    """

    def readProbability(self, instream):
        first_part = instream.read(200)
        if 'nmap' in first_part:
            return 50

    def parse(self, instream):
        xml = etree.parse(instream)
        root = xml.getroot()

        results = {}

        nmaprun = results['nmaprun'] = {}
        nmaprun.update(root.attrib)

        hosts = results['hosts'] = []
        
        for child in root:
            if child.tag == 'host':
                hosts.append(self._parseHost(child))
            elif child.tag == 'runstats':
                nmaprun['runstats'] = runstats = dict(child.attrib)
                for stat in child:
                    runstats[stat.tag] = dict(stat.attrib)
            else:
                nmaprun[child.tag] = self._parseNode(child)
        return results

    def _parseHost(self, host):
        ret = dict(host.attrib)
        ret.update({
            'addresses': [],
        })

        for tag in host:
            if tag.tag == 'status':
                ret['status'] = self._parseNode(tag)
            elif tag.tag == 'address':
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
                ret[tag.tag] = self._parseNode(tag)
        return ret

    def _parsePort(self, port):
        ret = dict(port.attrib)
        ret['port'] = int(ret.pop('portid'))
        for child in port:
            ret[child.tag] = self._parseNode(child)
        return ret

    def _parseHostScripts(self, xml):
        script = xml.find('.//script')
        ret = dict(script.attrib)
        data = ret['data'] = {}
        for elem in script:
            data[elem.attrib['key']] = elem.text
        return ret


    def _parseNode(self, node):
        ret = dict(node.attrib)
        children = []
        for child in node:
            children.append(self._parseNode(child))
        if children:
            ret['children'] = children
        return ret


