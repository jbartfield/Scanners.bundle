#
# Copyright (c) 2010-2011 Plex Development Team. All rights reserved.
#
import re, os, string
import Media, AudioFiles
import ID3, ID3v2
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.asf import ASF

various_artists = ['va', 'v/a', 'various', 'various artists', 'various artist(s)', 'various artitsen', 'verschiedene']
langDecodeMap = {'ko': ['euc_kr','cp949']}

def Scan(path, files, mediaList, subdirs, language=None):
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  if len(files) < 1: return
  albumTracks = []
  for f in files:
    try:
      artist = None
      (artist, album, title, track, disc, album_artist, compil) = getInfoFromTag(f, language)
      #print 'artist: ', artist, ' | album_artist: ', album_artist, ' | album: ', album, ' | disc: ', str(disc), ' | title: ', title, ' | compilation: ' + str(compil)
      if album_artist and album_artist.lower() in various_artists: #(compil == '1' and (album_artist is None or len(album_artist.strip()) == 0)) or (
        album_artist = 'Various Artists'
      if artist == None or len(artist.strip()) == 0:
        artist = '[Unknown Artist]'
      if album == None or len(album.strip()) == 0:
        album = '[Unknown Album]'
      if title == None or len(title) == 0: #use the filename for the title
        title = os.path.splitext(os.path.split(f)[1])[0]

      if track == None:
        # See if we have a tracknumber in the title and strip it.
        title = re.sub("^[0-9]{1,3}[ .-].+", '', title)
      else:
        # Check to see if the title starts with the track number and whack it.
        title = re.sub("^[ 0]*%s[ ]+" % track, '', title)

      title = title.strip(' -.')

      (allbutParentDir, parentDir) = os.path.split(os.path.dirname(f))
      if title.count(' - ') == 1 and artist == '[Unknown Artist]': # see if we can parse the title for artist - title
        (artist, title) = title.split(' - ')
        if len(artist) == 0: artist = '[Unknown Artist]'
      elif parentDir and parentDir.count(' - ') == 1 and (artist == '[Unknown Artist]' or album == '[Unknown Album]'):  #see if we can parse the folder dir for artist - album
        (pathArtist, pathAlbum) = parentDir.split(' - ')
        if artist == '[Unknown Artist]': artist = pathArtist
        if album == '[Unknown Album]': album = pathAlbum
      
      #make sure our last move is to encode to utf-8 before handing text back.
      t = Media.Track(cleanPass(artist), cleanPass(album), cleanPass(title), track, disc=disc, album_artist=cleanPass(album_artist))
      t.parts.append(f)
      albumTracks.append(t)
      #print 'Adding: [Artist: ' + artist + '] [Album: ' + album + '] [Title: ' + title + '] [Tracknumber: ' + str(track) + '] [Disk: ' + str(disc) + '] [Album Artist: ' + album_artist + '] [File: ' + f + ']'
    except:
      pass
      #print "Skipping (Metadata tag issue): ", f

  #add all tracks in dir, but first see if this might be a Various Artist album
  #first, let's group the albums in this folder together
  albumsDict = {}
  artistDict = {}
  for t in albumTracks:
    #add all the album names to a dictionary
    if albumsDict.has_key(t.album.lower()):
      albumsDict[t.album.lower()].append(t)
    else:
      albumsDict[t.album.lower()] = [t]
    #count instances of same artist names
    if artistDict.has_key(t.artist):
      artistDict[t.artist] +=1 
    else:
      artistDict[t.artist] = 1
      
  try: (maxArtistName, maxArtistCount) = sorted(artistDict.items(), key=lambda (k,v): (v,k))[-1]
  except: maxArtistCount = 0
    
  percentSameArtist = float(maxArtistCount)/len(albumTracks)
    
  #next, iterate through the album keys, and look at the tracks inside each album
  for a in albumsDict.keys():
    sameAlbum = True
    sameArtist = True
    prevAlbum = None
    prevArtist = None
    blankAlbumArtist = True
    for t in albumsDict[a]:
      if prevAlbum == None: prevAlbum = t.album
      if prevArtist == None: prevArtist = t.artist
      if prevAlbum.lower() != t.album.lower(): sameAlbum = False
      if prevArtist.lower() != t.artist.lower(): sameArtist = False
      prevAlbum = t.album
      prevArtist = t.artist
      if t.album_artist and len(t.album_artist.strip()) > 0:
        blankAlbumArtist = False
    
    if sameAlbum == True and sameArtist == False and blankAlbumArtist:
      if percentSameArtist < .9: #if the number of the same artist is less than X%, let's VA it (else, let's use the most common artist)
        newArtist = 'Various Artists'
      else:
        newArtist = maxArtistName
      for tt in albumsDict[a]:
        tt.album_artist = newArtist
        
  for t in albumTracks:
    mediaList.append(t)
  return

def cleanPass(t):
  try:
    t = t.strip().encode('utf-8')
  except:
    pass
  return t

def mp3tagGrabber(tag, filename, tagName, language, tagNameAlt=None, force=False):
  #try mutagen first
  t = None
  if tagNameAlt != None: tagNameMut = tagNameAlt
  else: tagNameMut = tagName
  if tag != None:
    t = mutagenGrabber(tag, tagNameMut, language)
  else:
    force = True
  if (t is None or len(t) == 0) and force == True:
    try: #then tagv2
      tagv2 = ID3v2.ID3v2(filename, language)
      t = tagv2.__dict__[tagName].decode('utf-8')
    except: 
      pass
    try: #else, tagv1
      if t is None or len(t) == 0:
        try:
          tagv1 = ID3.ID3(filename)
          t = tagv1.__dict__[tagName].decode('utf-8')
        except: 
          pass
    except: 
      pass
  return t

def mutagenGrabber(tag, tagName, language):
  try:
    t = tag[tagName][0]
    if language in langDecodeMap.iterkeys():
      for d in langDecodeMap[language]:
        try:
          t = t.decode(d).encode('utf-8')
          break
        except:
          try:
            t = t.encode('iso8859-1').decode(d)
            break
          except:
            t = t.encode('utf-8').decode('utf-8')
    else:
      try: t = t.encode('utf-8').decode('utf-8')
      except: pass      
  except:
    t = None
  return t

def cleanTrackAndDisk(inVal):
  try:
    outVal = inVal.split('/')[0]
    outVal = int(outVal)
  except:
    try: outVal = int(inVal)
    except: outVal = inVal

  return outVal

def getWMAstring(WMAtag):
  if str(type(WMAtag)).count('ASF') > 0:
    outStr = WMAtag.value.encode("utf-8")
  else:
    outStr = WMAtag
  return outStr
        
def getInfoFromTag(filename, language):
  compil = '0'
  tag = None
  if filename.lower().endswith("mp3"):
    try: 
      tag = EasyID3(filename)
    except: 
      return (None, None, None, None, None, None, None)
    artist = mp3tagGrabber(tag, filename, 'artist', language, force=True)
    album = mp3tagGrabber(tag, filename, 'album', language, force=True)
    title = mp3tagGrabber(tag, filename, 'title', language, force=True)
    track = cleanTrackAndDisk(mp3tagGrabber(tag, filename, 'track', language, 'tracknumber'))
    disc = cleanTrackAndDisk(mp3tagGrabber(tag, filename, 'disk', language, 'discnumber'))
    TPE2 = mp3tagGrabber(tag, filename, 'TPE2', language, 'performer')
    try: 
      compil = tag['compilation'][0]
    except:
      pass
    #print artist, album, title, track, disc, TPE2, compil
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("m4a") or filename.lower().endswith("m4b") or filename.lower().endswith("m4p"):
    try: 
      tag = EasyMP4(filename)
    except: 
      return (None, None, None, None, None, None, None)
  elif filename.lower().endswith("flac"):
    try: 
      tag = FLAC(filename)
    except: 
      return (None, None, None, None, None, None, None)
  elif filename.lower().endswith("ogg"):
    try: 
      tag = OggVorbis(filename)
    except: 
      return (None, None, None, None, None, None, None)
  elif filename.lower().endswith("wma"):
    try:
      tag = ASF(filename)
    except:
      return (None, None, None, None, None, None, None)
    artist = getWMAstring(mutagenGrabber(tag, 'Author', language))
    album = getWMAstring(mutagenGrabber(tag, 'WM/AlbumTitle', language))
    title = getWMAstring(mutagenGrabber(tag, 'Title', language))
    track = cleanTrackAndDisk(mutagenGrabber(tag, 'WM/TrackNumber', language))
    disc = cleanTrackAndDisk(mutagenGrabber(tag, 'WM/PartOfSet', language))
    TPE2 = getWMAstring(mutagenGrabber(tag, 'WM/AlbumArtist', language))
    return (artist, album, title, track, disc, TPE2, compil)
  else: #unsupported filetype
    return (None, None, None, None, None, None, None)
  artist = mutagenGrabber(tag, 'artist', language)
  album = mutagenGrabber(tag, 'album', language)
  title = mutagenGrabber(tag, 'title', language)
  track = cleanTrackAndDisk(mutagenGrabber(tag, 'tracknumber', language))
  disc = cleanTrackAndDisk(mutagenGrabber(tag, 'discnumber', language))
  TPE2 = mutagenGrabber(tag, 'albumartist', language)
  try:
    compil = tag['compilation'][0]
    if tag['compilation'][0] == True: compil = '1'
  except: 
    pass
  return (artist, album, title, track, disc, TPE2, compil)
