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

various_artists = ['va', 'v/a', 'various', 'various artists', 'various artist(s)', 'various artitsen', 'verschiedene']
langDecodeMap = {'ko': ['cp949','euc_kr']}

def Scan(path, files, mediaList, subdirs, language=None):
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  if len(files) < 1: return
  albumTracks = []
  for f in files:
    try:
      artist = None
      (artist, album, title, track, disc, album_artist, compil) = getInfoFromTag(f, language)
      #print 'artist: ', artist, 'album_artist: ', album_artist, 'album: ', album, 'title: ', title, 'compilation: ' + str(compil)
      if (compil == '1' and (album_artist is None or len(album_artist.strip()) == 0)) or (album_artist and album_artist.lower() in various_artists):
        album_artist = 'Various Artists'
      if artist == None or len(artist.strip()) == 0:
        artist = '[Unknown Artist]'
      if album == None or len(album.strip()) == 0:
        album = '[Unknown Album]'
      if title == None or len(title) == 0: #use the filename for the title
        title = os.path.splitext(os.path.split(f)[1])[0]
      if track == None:
        #see if we have a tracknumber in the title
        if title[0] in string.digits and title[1] in string.digits and title[2] in (string.punctuation + string.whitespace): # 2 digit tracknumber?
          track = int(title[0:2])
          title = title[3:]
        elif title[0] in string.digits and title[1] in (string.punctuation + string.whitespace): # 1 digit tracknumber?
          track = int(title[0])
          title = title[2:]
      else:
        # check to see if the tracknumber is in the title and remove it
        if str(track) == title[0]:
          title = title[1:]
          if title[0] in string.punctuation: title = title[1:]
        elif '0' + str(track) == title[:2]:
          title = title[2:]
          if title[0] in string.punctuation: title = title[1:]
        elif str(track) == title[:2]: 
          title = title[2:]
          if title[0] in string.punctuation: title = title[1:]
      title = title.strip()
      if title[:1] == '-': title = title[1:]
      (allbutParentDir, parentDir) = os.path.split(os.path.dirname(f))
      if title.count(' - ') == 1 and artist == '[Unknown Artist]': # see if we can parse the title for artist - title
        (artist, title) = title.split('-')
        if len(artist) == 0: artist = '[Unknown Artist]'
      elif parentDir and parentDir.count(' - ') == 1 and (artist == '[Unknown Artist]' or album == '[Unknown Album]'):  #see if we can parse the folder dir for artist - album
        (pathArtist, pathAlbum) = parentDir.split('-')
        if artist == '[Unknown Artist]': artist = pathArtist
        if album == '[Unknown Album]': album = pathAlbum

      t = Media.Track(artist.strip(), album.strip(), title.strip(), track, disc=disc, album_artist=album_artist)
      t.parts.append(f)
      albumTracks.append(t)
      #print 'Adding: [Artist: ' + artist + '] [Album: ' + album + '] [Title: ' + title + '] [Tracknumber: ' + str(track) + '] [Disk: ' + str(disc) + '] [Album Artist: ' + str(album_artist) + '] [File: ' + f + ']'
    except:
      pass
      #print "Skipping (Metadata tag issue): ", f
  #add all tracks in dir, but first see if this might be a Various Artist album
  #first, let's group the albums in this folder together
  albumsDict = {}
  for t in albumTracks:
    if albumsDict.has_key(t.album):
      albumsDict[t.album].append(t)
    else:
      albumsDict[t.album] = [t]
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
      for tt in albumsDict[a]:
        tt.album_artist = 'Various Artists'

  for t in albumTracks:
    mediaList.append(t)
      
  return

def mp3tagGrabber(tag, filename, tagName, language, tagNameAlt=None, force=False):
  #try mutagen first
  if tagNameAlt != None: tagNameMut = tagNameAlt
  else: tagNameMut = tagName
  if tag != None:
    t = mutagenGrabber(tag, tagNameMut, language)
  else:
    force = True
  if (t is None or len(t) == 0) and force == True:
    try: #then tagv2
      tagv2 = ID3v2.ID3v2(filename, language)
      t = tagv2.__dict__[tagName]
    except: pass
    try: #else, tagv1
      if t is None or len(t) == 0:
        try:
          tagv1 = ID3.ID3(filename)
          t = tagv1.__dict__[tagName]
        except:
          t = None
    except: pass
  return t

def mutagenGrabber(tag, tagName, language):
  try:
    t = tag[tagName][0]
    if language in langDecodeMap.iterkeys():
      for d in langDecodeMap[language]:
        try:
          t = t.encode('utf-8').decode(d).encode('utf-8')
          break
        except:
          try:
            t = t.encode('iso8859-1').decode(d).encode('utf-8')
            break
          except:
            t = t.encode('utf-8')
            pass
    else:
      try:
        t = t.encode('utf-8')
      except:
        pass      
  except:
    t = None
  return t

def cleanTrackAndDisk(inVal):
  try:
    outVal = inVal.split('/')[0]
    outVal = int(outVal)
  except:
    outVal = inVal
  return outVal
        
def getInfoFromTag(filename, language):
  compil = '0'
  if filename.lower().endswith("mp3"):
    try: tag = EasyID3(filename)
    except: tag = None
    artist = mp3tagGrabber(tag, filename, 'artist', language, force=True)
    album = mp3tagGrabber(tag, filename, 'album', language, force=True)
    title = mp3tagGrabber(tag, filename, 'title', language, force=True)
    track = cleanTrackAndDisk(mp3tagGrabber(tag, filename, 'track', language, 'tracknumber'))
    disc = cleanTrackAndDisk(mp3tagGrabber(tag, filename, 'disk', language, 'discnumber'))
    TPE2 = mp3tagGrabber(tag, filename, 'TPE2', language, 'performer')
    try: compil = tag['compilation'][0]
    except: pass
    #print artist, album, title, track, disc, TPE2, compil
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("m4a") or filename.lower().endswith("m4b") or filename.lower().endswith("m4p"):
    try: tag = EasyMP4(filename)
    except: return None
  elif filename.lower().endswith("flac"):
    try: tag = FLAC(filename)
    except: return None
  elif filename.lower().endswith("ogg"):
    try: tag = OggVorbis(filename)
    except: return None
  artist = mutagenGrabber(tag, 'artist', language)
  album = mutagenGrabber(tag, 'album', language)
  title = mutagenGrabber(tag, 'title', language)
  track = cleanTrackAndDisk(mutagenGrabber(tag, 'tracknumber', language))
  disc = cleanTrackAndDisk(mutagenGrabber(tag, 'discnumber', language))
  TPE2 = mutagenGrabber(tag, 'performer', language)
  try:
    compil = tag['compilation'][0]
    if tag['compilation'][0] == True: compil = '1'
  except: pass
  return (artist, album, title, track, disc, TPE2, compil)
