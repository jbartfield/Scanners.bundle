import urllib
from xml.dom import minidom
import Media, AudioFiles

Virtual = True

def Scan(path, files, mediaList, subdirs, language=None):
  if len(path) == 0:
    # Top level, artists.
    dom = minidom.parse(urllib.urlopen('http://127.0.0.1:32400/music/iTunes/Artists'))
    for artist in dom.getElementsByTagName('Artist'):
      subdirs.append('/' + artist.getAttribute('key'))
  else:
    paths = path.split('/')
    if len(paths) == 1:
      # Albums for artist.
      dom = minidom.parse(urllib.urlopen('http://127.0.0.1:32400/music/iTunes/Artists/%s' % paths[0]))
      for album in dom.getElementsByTagName('Album'):
        subdirs.append('/' + path + '/' + album.getAttribute('key'))
    elif len(paths) == 2:
      # Tracks, let's finally add it.
      dom = minidom.parse(urllib.urlopen('http://127.0.0.1:32400/music/iTunes/Artists/%s/%s' % (paths[0], paths[1])))
      artist_album_map = {}
      compilation_count = 0
      for track in dom.getElementsByTagName('Track'):
        # Figure out album artist.
        album_artist = track.getAttribute('albumArtist').strip()
        artist_album_map[album_artist] = True
        if len(album_artist) == 0: album_artist = None
        else: album_artist = album_artist.encode('utf-8')
        
        # Add the track.
        t = Media.Track(artist = track.getAttribute('artist').encode('utf-8'),
                        album = track.getAttribute('album').encode('utf-8'),
                        title = track.getAttribute('track').encode('utf-8'),
                        index = int(track.getAttribute('index')),
                        album_artist = album_artist,
                        disc = int(track.getAttribute('disc')))
        if track.getAttribute('compilation') == '1': compilation_count = compilation_count + 1
        t.parts.append(track.getAttribute('file'))
        mediaList.append(t)
      
      # If we're listed as a compilation, make sure all album artists are there and the same.
      if compilation_count > 0 and (len(artist_album_map) > 1 or len(artist_album_map.keys()[0])):
        for t in mediaList:
          t.album_artist = 'Various Artists'
        