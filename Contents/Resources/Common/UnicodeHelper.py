import string

_encodings = ['iso8859-1', 'utf-16', 'utf-16be', 'utf-8']

def fixEncoding(theString):
  encoding = ord(theString[0])
  if 0 <= encoding < len(_encodings):
    value = theString[1:].decode(_encodings[encoding]).encode("utf-8")
  else:
    value = theString

  if value:
    value = value.strip('\0')

  return value
