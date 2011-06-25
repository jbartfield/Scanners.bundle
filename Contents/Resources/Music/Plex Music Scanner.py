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

nextTrackNumber = {}
albumArtistTrackNumbers = {}

def Scan(path, files, mediaList, subdirs, language=None):
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  if len(files) < 1: return
  albumTracks = []
  #lastDirname = None
  for f in files:
    #try:
      #print 'DIRNAME: ' + os.path.dirname(f)
      #print 'LASTNAME: ' + str(lastDirname)
      #if not lastDirname or os.path.dirname(f) != lastDirname:
      #  print '!!!!!'
      #  for t in albumTracks:
      #    print t.artist
      #    mediaList.append(t)
      #  albumTracks = []
      #else:
      #  lastDirname = os.path.dirname(f)
      
      artist = None
      (artist, album, title, track, disc, album_artist, compil) = getInfoFromTag(f, language)
      print 'artist: ', artist, 'album: ', album, 'title: ', title, 'compilation: ' + str(compil)
      if compil == '1':
        artist = 'Various Artists'
      if artist == None or len(artist.strip()) == 0:
        artist = '[Unknown Artist]'
      if album == None or len(album.strip()) == 0:
        album = '[Unknown Album]'
      if title == None or len(title) == 0: #use the filename for the title
        title = os.path.splitext(os.path.split(f)[1])[0]
      if track == None:
        #see if we have a tracknumber in the title
        if title[0] in string.digits and title[1] in string.digits and title[2] in (string.punctuation + string.whitespace): # 2 digit tracknumber?
          track = int(title[0:1])
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
      if title.count('-') == 1 and artist == '[Unknown Artist]': # see if we can parse the title for artist - title
        (artist, title) = title.split('-')
        if len(artist) == 0: artist = '[Unknown Artist]'
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
      print 'Adding: [Artist: ' + artist + '] [Album: ' + album + '] [Title: ' + title + '] [Tracknumber: ' + str(track) + '] [Disk: ' + str(disc) + '] [Album Artist: ' + str(album_artist) + '] [File: ' + f + ']'
    #except:
      print "Skipping (Metadata tag issue): ", f
  #add all tracks in dir
  sameAlbum = True
  sameArtist = True
  prevAlbum = None
  prevArtist = None
  for t in albumTracks:
    if prevAlbum == None: prevAlbum = t.album
    if prevArtist == None: prevArtist = t.artist
    if prevAlbum != t.album: sameAlbum = False
    if prevArtist != t.artist: sameArtist = False
    prevAlbum = t.album
    prevArtist = t.artist
  if sameAlbum == True and sameArtist == False:
    for t in albumTracks:
      t.artist = 'Various Artists'
  for t in albumTracks:  
    mediaList.append(t)
  return
        
def getInfoFromTag(filename, language):
  "= (artist, album, title, track, disk, 'album-artist') for the song at filename.  Returns None if no valid tag is found"
  compil = '0'
  if filename.lower().endswith("mp3"):
    try:
      try:
        tagMutagen = EasyID3(filename)
        compil = tagMutagen['compilation'][0]
      except:
        pass
      tag = ID3v2.ID3v2(filename, language)
      if tag.isOK() and len(tag.artist) != 0 and len(tag.album) != 0:
        if tag.TPE2 and tag.TPE2.lower() == tag.artist.lower():
          tag.TPE2 = None
        return (tag.artist, tag.album, tag.title, int(tag.track), tag.disk, tag.TPE2, compil)
      tag = ID3.ID3(filename)
      try: artist = tag.artist
      except: artist = None
      try: album = tag.album
      except: album = None
      if (artist == None or len(artist) == 0) and (album == None or len(album) == 0):
        raise #try mutagen
      try: title = tag.title
      except: title = None
      try: track = int(tag.track)
      except: track = None
      try: disc = tag.disk
      except: disc = None
      return (artist, album, title, track, disc, None, compil)
    except:
      #try mutagen
      if tagMutagen:
        tag = tagMutagen
      else:
        try: tag = EasyID3(filename)
        except: pass
      try: artist = tag['artist'][0].encode('utf-8')
      except: artist = None
      try: album = tag['album'][0].encode('utf-8')
      except: album = None
      try: title = tag['title'][0].encode('utf-8')
      except: title = None
      try:
        track = tag['tracknumber'][0]
        track = track.split('/')[0]
        track = int(track)
      except: track = None
      try: disc = int(tag['discnumber'][0])
      except: disc = None
      try: TPE2 = tag['performer'][0].encode('utf-8')
      except: TPE2 = None
      return (artist, album, title, track, disc, TPE2, compil)
    
  elif filename.lower().endswith("m4a") or filename.lower().endswith("m4b") or filename.lower().endswith("m4p"):
    try: tag = EasyMP4(filename)
    except: return None
    try: artist = tag['artist'][0].encode('utf-8')
    except: artist = None
    try: album = tag['album'][0].encode('utf-8')
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try:
      track = tag['tracknumber'][0]
      track = track.split('/')[0]
      track = int(track)
    except: track = None
    try: disc = int(tag['discnumber'][0])
    except: disc = None
    try: TPE2 = tag['performer']
    except: TPE2 = None
    return (artist, album, title, track, disc, TPE2, compil)
  elif filename.lower().endswith("flac"):
    try: tag = FLAC(filename)
    except: return None
    try: artist = tag['artist'][0].encode('utf-8')
    except: artist = None
    try: album = tag['album'][0].encode('utf-8')
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try: track = int(tag['tracknumber'][0])
    except: track = None
    try: disc = int(tag['discnumber'][0])
    except: disc = None
    return (artist, album, title, track, disc, None, compil)
  elif filename.lower().endswith("ogg"):
    try: tag = OggVorbis(filename)
    except: return None
    try: artist = tag['artist'][0].encode('utf-8')
    except: artist = None
    try: album = tag['album'][0].encode('utf-8')
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try: track = int(tag['tracknumber'][0])
    except: track = None
    try: disc = int(tag['discnumber'][0])
    except: disc = None
    return (artist, album, title, track, disc, None, compil)