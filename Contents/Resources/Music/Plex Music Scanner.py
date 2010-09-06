#
# Copyright (c) 2010 Plex Development Team. All rights reserved.
#
import re, os, os.path
import Media, AudioFiles
import ID3, ID3v2, M4ATags

# 01 - Track.mp3
trackRx1 = '([0-9]{2})[-. ]*(.*)\.[a-z0-9]{3,4}'

# Artist - 01 - Track.mp3
trackRx2 = '.*[-. ]+([0-9]{2})[-\. ]+(.+)\.[a-z0-9]{3,4}'

# 01 - Artist - Track.mp3 ALSO CHECKED IN getTitleTrack

trackRxs = [trackRx1, trackRx2]

def Scan(path, files, mediaList, subdirs):
  
  # Scan for audio files.
  AudioFiles.Scan(path, files, mediaList, subdirs)
  paths = path.split('/')

  if len(files) < 1:
    return

  # Looks like an album
  if len(path) > 1 and len(path[0]) > 0 and 0 < len(files) < 50:
    try:
      (FArtist, FAlbum, FTitle, FTrack, FDisk, FTPE2) = getInfoFromTag(files[0])
      (LArtist, LAlbum, LTitle, LTrack, LDisk, LTPE2) = getInfoFromTag(files[-1])
    except:            # if either getInfoFromTag(...) == None
      FArtist = 'a'    # will short circuit and
      LArtist = 'b'    # skip the next if branch

    #           Check artist                               Check album
    if FArtist.lower() == LArtist.lower() and FAlbum.lower() == FAlbum.lower() and len(FArtist) > 0 and len(FAlbum) > 0:
      appendTrack(mediaList, files[0], FArtist, FAlbum, FTitle, FTrack, FDisk, FTPE2)
      appendTrack(mediaList, files[-1], LArtist, LAlbum, LTitle, LTrack, LDisk, LTPE2)
      
      #          Check disks            check TPE2
      if (FDisk and FDisk != LDisk) or FTPE2 != LTPE2:
        for f in files[1:-1]:
          appendTrackFromTag(mediaList, f)
        return
      else:
        appendAlbum(mediaList, files[1:-1], FArtist, FAlbum, FDisk, FTPE2)
        return

  # Can't get rid of the next part outright because at the moment it is the only
  # way an album with a good directory structure will ever be added if it doesn't
  # have a file extension that has tags we currently support
  
  # TWEAK: We'll pass on these for now because they could have evil naming. 
  # The philosophy is (for now, at least): Add what we know is good, ignore 
  # what's not.
  #
    
  # Artist / Album.
  #if len(paths) == 2 and len(subdirs) == 0:
  #  first = getInfoFromTag(files[0])
  #  if first == None or first[0].lower() == paths[0].lower():
  #    TPE2 = None
  #   if "Various Artists" in path:
  #      TPE2 = "Various Artists"
  #    appendAlbum(mediaList, files, paths[0], paths[1], TPE2=TPE2)
  #    return


  # This seems like a decent compromise.  I have a bunch of songs that are just one
  # song off of an album that won't get picked up without something like this

  # TWEAK: We don't want to take standalone files for now, just well-defined albums.

  #if len(files) < 3:
  #  for f in files:
  #    appendTrackFromTag(mediaList, f)
  #  return


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

  return info

def getInfoFromTag(filename):
  "= (artist, album, title, track, disk, 'album-artist') for the song at filename.  Returns None if no valid tag is found"
  if filename.endswith("mp3"):
    try:
      tag = ID3v2.ID3v2(filename)
      if tag.isOK() and len(tag.artist) != 0 and len(tag.album) != 0:
        if tag.TPE2 and tag.TPE2.lower() == tag.artist:
          tag.TPE2 = None
        return (tag.artist, tag.album, tag.title, int(tag.track), tag.disk, tag.TPE2)

      tag = ID3.ID3(filename)
      if tag.has_tag and len(tag.artist) != 0 and len(tag.album) != 0:
        return (tag.artist, tag.album, tag.title, int(tag.track), None, None)
      return None
    except:
      return None

  if filename.endswith("m4a") or filename.endswith("m4b"):
    try:
      tag = M4ATags.M4ATags(filename)
      artist = tag['Artist']
      album = tag['Album']
      title = tag['Title']
      track = int(tag['Track'])
      return (artist, album, title, track, None, None)
    except:
      return None

def appendTrack(mediaList, f, artist, album, title, track, disk=None, TPE2=None):
  t = Media.Track(artist, album, title, track, disc=disk, album_artist=TPE2)
  if len(artist) > 0 and len(album) > 0:
    t.parts.append(f)
    mediaList.append(t)

def appendAlbum(mediaList, files, artist, album, disk=None, TPE2=None):
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
      print "Slow path for", f
      appendTrackFromTag(mediaList, f)

def appendTrackFromTag(mediaList, f):
  info = getInfoFromTag(f)
  if info:
    appendTrack(mediaList, f, *info)

