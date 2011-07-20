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
  nextTrackNumber = {}
  albumArtistTrackNumbers = {}
  
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
      if track == None: # still None? make up a tracknumber to avoid a single track getting multiple parts
        if not nextTrackNumber.has_key(artist+album):
          nextTrackNumber[artist+album] = 200
        track = nextTrackNumber[artist+album]
        nextTrackNumber[artist+album]+=1
      else: # let's make sure we aren't repeating a tracknumber
        if albumArtistTrackNumbers.has_key(artist+album):
          if track in albumArtistTrackNumbers[artist+album]:
            if max(albumArtistTrackNumbers[artist+album]) < 100:
              track = track + 100
            else:
              track = max(albumArtistTrackNumbers[artist+album]) + 1
      if albumArtistTrackNumbers.has_key(artist+album):
        albumArtistTrackNumbers[artist+album].append(track)
      else:
        albumArtistTrackNumbers[artist+album] = [track]
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
      for t in albumTracks:
        t.album_artist = 'Various Artists'
    for t in albumTracks:
      mediaList.append(t)
  return

def tagGrabber(tagv2, tagv1, alt, tagName, language, tagNameAlt=None):
  #mutagen first
  if tagNameAlt != None:
    tagName = tagNameAlt
  t = mutagenGrabber(alt, tagName, language)
  try:
    if t is None or len(t) == 0:
      try: #then tagv2
        t = tagv2.__dict__[tagName]
      except: pass
      try: #else, tagv1
        if t is None or len(t) == 0:
          try:
            t = tagv1.__dict__[tagName]
          except:
            t = None
      except: pass
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
    try:
      tagMutagen = EasyID3(filename)
      compil = tagMutagen['compilation'][0]
    except:
      pass
    tagv2 = ID3v2.ID3v2(filename, language)
    tagv1 = ID3.ID3(filename)
    if tagMutagen:
      tagAlt = tagMutagen
    else:
      try:
        tagAlt = EasyID3(filename)
      except: 
        tagAlt = None
    artist = tagGrabber(tagv2, tagv1, tagAlt, 'artist', language)
    album = tagGrabber(tagv2, tagv1, tagAlt, 'album', language)
    title = tagGrabber(tagv2, tagv1, tagAlt, 'title', language)
    track = cleanTrackAndDisk(tagGrabber(tagv2, tagv1, tagAlt, 'track', language, 'tracknumber'))
    disc = cleanTrackAndDisk(tagGrabber(tagv2, tagv1, tagAlt, 'disk', language, 'discnumber'))
    TPE2 = tagGrabber(tagv2, tagv1, tagAlt, 'performer', language)
    if TPE2 is None or len(TPE2) == 0:
      try:
        TPE2 = tagv2.TPE2
      except:
        TPE2 = None
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("m4a") or filename.lower().endswith("m4b") or filename.lower().endswith("m4p"):
    try: tag = EasyMP4(filename)
    except: return None
    artist = mutagenGrabber(tag, 'artist', language)
    album = mutagenGrabber(tag, 'album', language)
    title = mutagenGrabber(tag, 'title', language)
    track = cleanTrackAndDisk(mutagenGrabber(tag, 'tracknumber', language))
    disc = cleanTrackAndDisk(mutagenGrabber(tag, 'discnumber', language))
    TPE2 = mutagenGrabber(tag, 'performer')
    #not sure on this: this was replacing TPE2 before --> TPE2 = tag['albumartist'][0].encode('utf-8')
    try:
      if tag['compilation'] == True: compil = '1'
    except: pass
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("flac"):
    try: tag = FLAC(filename)
    except: return None
    artist = mutagenGrabber(tag, 'artist', language)
    album = mutagenGrabber(tag, 'album', language)
    title = mutagenGrabber(tag, 'title', language)
    track = cleanTrackAndDisk(mutagenGrabber(tag, 'tracknumber', language))
    disc = cleanTrackAndDisk(mutagenGrabber(tag, 'discnumber', language))
    TPE2 = mutagenGrabber(tag, 'performer', language)
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("ogg"):
    try: tag = OggVorbis(filename)
    except: return None
    artist = mutagenGrabber(tag, 'artist', language)
    album = mutagenGrabber(tag, 'album', language)
    title = mutagenGrabber(tag, 'title', language)
    track = cleanTrackAndDisk(mutagenGrabber(tag, 'tracknumber', language))
    disc = cleanTrackAndDisk(mutagenGrabber(tag, 'discnumber', language))
    TPE2 = mutagenGrabber(tag, 'performer', language)
    return (artist, album, title, track, disc, TPE2, compil)