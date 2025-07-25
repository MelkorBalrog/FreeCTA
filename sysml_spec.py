import re
import os


def load_sysml_properties():
    path = os.path.join(os.path.dirname(__file__), 'SysML.xmi')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    start = text.find('<xmi:XMI')
    if start == -1:
        return {}
    text = text[start:]
    class_pattern = re.compile(r'<packagedElement[^>]*xmi:type="uml:Class"[^>]*name="([^"]+)"')
    attr_pattern = re.compile(r'<ownedAttribute[^>]*name="([^"]+)"')
    props = {}
    for m in class_pattern.finditer(text):
        name = m.group(1)
        end = text.find('</packagedElement>', m.end())
        if end == -1:
            continue
        block = text[m.end():end]
        attrs = attr_pattern.findall(block)
        props[name] = attrs
    return props

SYSML_PROPERTIES = load_sysml_properties()
if 'BlockUsage' not in SYSML_PROPERTIES:
    SYSML_PROPERTIES['BlockUsage'] = [
        'valueProperties',
        'partProperties',
        'referenceProperties',
        'ports',
        'constraintProperties',
        'operations',
    ]
if 'PortUsage' not in SYSML_PROPERTIES:
    SYSML_PROPERTIES['PortUsage'] = []
for p in ('direction', 'flow'):
    if p not in SYSML_PROPERTIES['PortUsage']:
        SYSML_PROPERTIES['PortUsage'].append(p)
