#
# Copyright (c) 2010-2011 Plex Development Team. All rights reserved.
#
import re, os
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
  for f in files:
    try:
      (artist, album, title, track, disk, TPE2) = getInfoFromTag(f, language)
      appendTrack(mediaList, f, artist, album, title, track, disk, TPE2)
      print 'Adding: [Artist: ' + artist + '] [Album: ' + album + '] [Title: ' + title + '] [Tracknumber: ' + str(track) + '] [Disk: ' + str(disk) + '] [Album Artist: ' + str(TPE2) + '] [File: ' + f + ']'
    except:
      print "Skipping (Metadata tag issue): ", f
  return

def appendTrack(mediaList, f, artist, album, title, track, disk=None, TPE2=None):
  t = Media.Track(artist, album, title, track, disc=disk, album_artist=TPE2)
  if len(artist) > 0 and len(album) > 0:
    t.parts.append(f)
    mediaList.append(t)
        
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
      if len(artist) == 0: raise
      try: 
        album = tag.album
        if len(album) == 0:
          album = '[Unknown]'
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
      try: 
        album = tag['album'][0].encode('utf-8')
        if len(album) == 0:
          album = '[Unknown]'
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
    try: 
      album = tag['album'][0].encode('utf-8')
      if len(album) == 0:
        album = '[Unknown]'
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
    try: 
      album = tag['album'][0].encode('utf-8')
      if len(album) == 0:
        album = '[Unknown]'
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
    try: 
      album = tag['album'][0].encode('utf-8')
      if len(album) == 0:
        album = '[Unknown]'
    except: album = None
    try: title = tag['title'][0].encode('utf-8')
    except: title = None
    try: track = int(tag['tracknumber'][0])
    except: track = None
    try: disc = int(tag['discnumber'][0])
    except: disc = None
    return (artist, album, title, track, disc, None)