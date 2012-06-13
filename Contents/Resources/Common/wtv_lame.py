import re
from datetime import datetime

def WTV_Metadata(path):
  f = open(path,'rb')
  metaHeader = f.read(80000)
  # Search for printable ASCII characters encoded as UTF-16LE.
  pat = re.compile(ur'(?:[\x20-\x7E][\x00]){3,}')
  tags = [w.decode('utf-16le') for w in pat.findall(metaHeader)]
  show = tags[tags.index('Title')+1].encode('utf-8')
  origDate = tags[tags.index('WM/MediaOriginalBroadcastDateTime')+1]
  released_at = datetime.strptime(origDate.replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S').date()
  year = int(released_at.year)
  title = tags[tags.index('WM/SubTitle')+1].encode('utf-8')
  if title[:3] == 'WM/':
    title = ''
  return (show, year, title, released_at)