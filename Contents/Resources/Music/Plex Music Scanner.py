#
# Copyright (c) 2010-2011 Plex Development Team. All rights reserved.
#
import re, os, os.path
import Media, AudioFiles
import ID3, ID3v2, M4ATags
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
import unicodedata

# 01 - Track.mp3
trackRx1 = '([0-9]{2})[-. _]*(.*)\.[a-z0-9]{3,4}'

# Artist - 01 - Track.mp3
trackRx2 = '.*[-. _]+([0-9]{2})[-\. ]+(.+)\.[a-z0-9]{3,4}'

# 01 - Artist - Track.mp3 ALSO CHECKED IN getTitleTrack

trackRxs = [trackRx1, trackRx2]

def Scan(path, files, mediaList, subdirs, language=None):
  
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  paths = path.split('/')
  
  if len(files) < 1:
    return
    
  # Root level music
  if len(path) == 0:
    for file in files:
      try:
        (FArtist, FAlbum, FTitle, FTrack, FDisk, FTPE2) = getInfoFromTag(file, language)
        appendAlbum(mediaList, [file], FArtist, FAlbum, FDisk, FTPE2, language)
      except:
        print "No tag for", file
    return

  # Looks like an album
  if len(path) > 1 and len(path[0]) > 0 and 0 < len(files) < 50:
    try:
      (FArtist, FAlbum, FTitle, FTrack, FDisk, FTPE2) = getInfoFromTag(files[0], language)
      (LArtist, LAlbum, LTitle, LTrack, LDisk, LTPE2) = getInfoFromTag(files[-1], language)
    except:            # if either getInfoFromTag(...) == None
      FArtist = 'a'    # will short circuit and
      LArtist = 'b'    # skip the next if branch
    #           Check artist                               Check album
    if FArtist.lower() == LArtist.lower() and FAlbum.lower() == FAlbum.lower() and len(FArtist) > 0 and len(FAlbum) > 0:
      # Add the first and last tracks.
      appendTrack(mediaList, files[0], FArtist, FAlbum, FTitle, FTrack, FDisk, FTPE2)
      appendTrack(mediaList, files[-1], LArtist, LAlbum, LTitle, LTrack, LDisk, LTPE2)
      #          Check disks            check TPE2
      if (FDisk and FDisk != LDisk) or FTPE2 != LTPE2:
        for f in files[1:-1]:
          appendTrackFromTag(mediaList, f, language)
      else:
        appendAlbum(mediaList, files[1:-1], FArtist, FAlbum, FDisk, FTPE2, language)
    else:
      # Add all the tracks.
      for file in files:
        appendTrackFromTag(mediaList, file, language)
      
def getTitleTrack(filename):
  """
  = [title, track] for the song at filename by using the regexs in trackRxs.
    Most consecutive calls in the same album match the same rx, so in an
    attempt to be self-optimized the match is moved to the front of the list.
  """
  file = os.path.basename(filename)
  reorder = False
  for rx in trackRxs:
    match = re.match(rx, file, re.IGNORECASE)
    if match:
      info = [match.group(2), int(match.group(1))]
      break
    reorder = True
  else:
    return None
  if reorder:
    trackRxs.remove(rx)
    trackRxs.insert(0, rx)
  # 01 - Artist - Track.mp3
  index = info[0].rfind("-")
  if index != -1 and index + 1 != len(info[0]):
    info[0] = info[0][(index+1):].strip()
  # Precompose.
  info[0] = unicodedata.normalize('NFKC', info[0].decode('utf-8')).encode('utf-8')
  return info

def getInfoFromTag(filename, language):
  "= (artist, album, title, track, disk, 'album-artist') for the song at filename.  Returns None if no valid tag is found"
  if filename.lower().endswith("mp3"):
    try:
      tag = ID3v2.ID3v2(filename, language)
      if tag.isOK() and len(tag.artist) != 0 and len(tag.album) != 0:
        if tag.TPE2 and tag.TPE2.lower() == tag.artist:
          tag.TPE2 = None
        return (tag.artist, tag.album, tag.title, int(tag.track), tag.disk, tag.TPE2)
      tag = ID3.ID3(filename)
      try: artist = tag.artist
      except: artist = None
      try: 
        album = tag.album
        if len(album) == 0:
          album = '[Unknown]'
      except: album = '-'
      try: title = tag.title
      except: title = None
      try: track = int(tag.track)
      except: track = None
      return (artist, album, title, track, None, None)
    except:
      return None
  elif filename.lower().endswith("m4a") or filename.lower().endswith("m4b"):
    try: tag = M4ATags.M4ATags(filename)
    except: return None
    try: artist = tag['Artist']
    except: artist = None
    try: 
      album = tag['Album']
      if len(album) == 0:
        album = '[Unknown]'
    except: album = None
    try: title = tag['Title']
    except: title = None
    try: track = int(tag['Track'])
    except: track = None
    return (artist, album, title, track, None, None)
  elif filename.lower().endswith("flac"):
    try: tag = FLAC(filename)
    except: return None
    try: artist = tag['artist'][0].encode('utf-8')
    except: artist = None
    try: 
      album = tag['album'][0].encode('utf-8')
      if len(album) == 0:
        album = '[Unknown]'
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try: track = int(tag['tracknumber'][0])
    except: track = None
    return (artist, album, title, track, None, None)
  elif filename.lower().endswith("ogg"):
    try: tag = OggVorbis(filename)
    except: return None
    try: artist = tag['artist'][0].encode('utf-8')
    except: artist = None
    try: 
      album = tag['album'][0].encode('utf-8')
      if len(album) == 0:
        album = '[Unknown]'
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try: track = int(tag['tracknumber'][0])
    except: track = None
    return (artist, album, title, track, None, None)
    
def appendTrack(mediaList, f, artist, album, title, track, disk=None, TPE2=None):
  t = Media.Track(artist, album, title, track, disc=disk, album_artist=TPE2)
  if len(artist) > 0 and len(album) > 0:
    t.parts.append(f)
    mediaList.append(t)

def appendAlbum(mediaList, files, artist, album, disk=None, TPE2=None, language=None):
  """
  Adds all the files to the mediaList with the given artist and album.  If it can't get the title and track, then it attempts
  to add the file by using tags.  As a result, a file might potentially be added with a different artist/album than those 
  passed as parameters.
  """
  for f in files:
    info = getTitleTrack(f)
    if info:
      appendTrack(mediaList, f, artist, album, info[0], info[1], disk, TPE2)
    else:
      appendTrackFromTag(mediaList, f, language)

def appendTrackFromTag(mediaList, f, language):
  info = getInfoFromTag(f, language)
  if info:
    appendTrack(mediaList, f, *info)