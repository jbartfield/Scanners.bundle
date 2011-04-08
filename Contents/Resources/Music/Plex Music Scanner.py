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

def Scan(path, files, mediaList, subdirs, language=None):
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  if len(files) < 1: return
  nextTrackNumber = {}
  for f in files:
    try:
      (artist, album, title, track, disc, album_artist) = getInfoFromTag(f, language)
      if artist == None or len(artist) == 0:
        artist = '[Unknown Artist]'
      if album == None or len(album) == 0:
        album = '[Unknown Album]'
      if title == None or len(title) == 0:
        title = os.path.splitext(os.path.split(f)[1])[0]
        if title.count('-') == 1 and artist == '[Unknown Artist]':
          (artist, title) = title.split('-')
      if track == None:
        #see if we have a tracknumber in the title
        if title[0] in string.digits and title[1] in string.digits and title[2] in (string.punctuation + string.whitespace): # 2 digit tracknumber?
          track = int(title[0:1])
          title = title[3:]
        elif title[0] in string.digits and title[1] in (string.punctuation + string.whitespace): # 1 digit tracknumber?
          track = int(title[0])
          title = title[2:]
      else:
        #check to see if the tracknumber is in the title and remove it
        if str(track) == title[0]: 
          title = title[1:]
          if title[0] in string.punctuation: title = title[1:]
        elif '0' + str(track) == title[:2]:
          title = title[2:]
          if title[0] in string.punctuation: title = title[1:]
        elif str(track) == title[:2]: 
          title = title[2:]
          if title[0] in string.punctuation: title = title[1:]
      if track == None: #still None? make up a tracknumber to avoid a single track getting multiple parts
        if not nextTrackNumber.has_key(artist+album):
          nextTrackNumber[artist+album] = 100
        track = nextTrackNumber[artist+album]
        nextTrackNumber[artist+album]+=1
      t = Media.Track(artist.strip(), album.strip(), title.strip(), track, disc=disc, album_artist=album_artist)
      #************************* check here to make sure we aren't adding an additional part (increment the track number somehow, maybe by 100)
      t.parts.append(f)
      mediaList.append(t)
      print 'Adding: [Artist: ' + artist + '] [Album: ' + album + '] [Title: ' + title + '] [Tracknumber: ' + str(track) + '] [Disk: ' + str(disc) + '] [Album Artist: ' + str(album_artist) + '] [File: ' + f + ']'
    except:
      print "Skipping (Metadata tag issue): ", f
  return
        
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
      try:
        artist = tag.artist
      except: artist = None
      try: album = tag.album
      except: album = '-'
      try: title = tag.title
      except: title = None
      try: track = int(tag.track)
      except: track = None
      try: disc = tag.disk
      except: disc = None
      return (artist, album, title, track, disc, None)
    except:
      #try mutagen
      try: tag = EasyID3(filename)
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
      try: TPE2 = tag['performer'][0].encode('utf-8')
      except: TPE2 = None
      return (artist, album, title, track, disc, TPE2)
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
    return (artist, album, title, track, disc, TPE2)
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
    return (artist, album, title, track, disc, None)
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
    return (artist, album, title, track, disc, None)