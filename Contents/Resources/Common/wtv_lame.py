import re

def WTV_Metadata(path):
  f = open(path,'rb')
  metaHeader = f.read(80000)
  metaHeader = metaHeader[metaHeader.find('\x57\x00\x4D\x00\x2F\x00'):]
  # Search for printable ASCII characters encoded as UTF-16LE.
  tags = metaHeader.split('\x5A\xFE\xD7\x6D\xC8\x1D\x8F\x4A\x99\x22\xFA\xB1\x1C\x38\x14\x53')
  pat = re.compile(ur'(?:[\x20-\x7E][\x00]){2,}')
  tagDict = {}
  for z in tags:
    z = [w.decode('utf-16le').encode('utf-8') for w in pat.findall(z)]
    if len(z)==1:
      tagDict[z[0]] = ''
    elif len(z)==2:
      tagDict[z[0]] = z[1]
    else:
      continue
  return tagDict