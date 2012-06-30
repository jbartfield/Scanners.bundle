import urllib, re
from xml.dom import minidom
import Media, AudioFiles

Virtual = True

def Scan(path, files, mediaList, subdirs, language=None):
  if len(path) == 0:
    # Top level, albums.
    dom = minidom.parse(urllib.urlopen('http://127.0.0.1:32400/music/iTunes/Albums'))
    for album in sorted(dom.getElementsByTagName('Album'), key=lambda album: album.getAttribute('artist').lower() + album.getAttribute('album').lower()):
      subdirs.append('/' + album.getAttribute('key'))
  else:
    # Tracks.
    paths = path.split('/')
    dom = minidom.parse(urllib.urlopen('http://127.0.0.1:32400/music/iTunes/Albums/%s' % paths[0]))
    artist_album_map = {}
    compilation_count = 0
    for track in dom.getElementsByTagName('Track'):
      # Figure out album artist.
      album_artist = track.getAttribute('albumArtist').strip()
      artist_album_map[album_artist] = True
      if len(album_artist) == 0: album_artist = None
      else: album_artist = album_artist.encode('utf-8')
      
      # Track index, do a bit of extra work.
      index = int(track.getAttribute('index'))
      file = track.getAttribute('file').split('/')[-1]
      if index == 0:
        try: index = int(re.findall('[.\-]+[ ]*([0-9]{2})[ ]*[.\-]', file)[0])
        except: 
          try: index = int(re.findall('^([0-9]{2})[ .\-]', file)[0])
          except: pass
      
      # Add the track.
      t = Media.Track(artist = track.getAttribute('artist').encode('utf-8'),
                      album = track.getAttribute('album').encode('utf-8'),
                      title = track.getAttribute('track').encode('utf-8'),
                      index = index,
                      album_artist = album_artist,
                      disc = int(track.getAttribute('disc')))
      if track.getAttribute('compilation') == '1': compilation_count = compilation_count + 1
      t.parts.append(urllib.unquote(track.getAttribute('file')).encode('utf-8'))
      mediaList.append(t)
    
    # If we're listed as a compilation, make sure all album artists are there and the same.
    if compilation_count > 0 and (len(artist_album_map) > 1 or len(artist_album_map.keys()[0]) == 0):
      for t in mediaList:
        t.album_artist = 'Various Artists'
