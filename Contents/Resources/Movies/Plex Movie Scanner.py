#
# Copyright (c) 2010 Plex Development Team. All rights reserved.
#
import re, os, os.path
import Media, VideoFiles, Stack
SeriesScanner = __import__('Plex Series Scanner')

nice_match = '(.+) [\(\[]([1-2][0-9]{3})[\)\]]'
standalone_tv_regexs = [ '(.*?)( \(([0-9]+)\))? - ([0-9])+x([0-9]+)(-[0-9]+[Xx]([0-9]+))? - (.*)' ]

# Scans through files, and add to the media list.
def Scan(path, files, mediaList, subdirs):
  
  # Scan for video files.
  VideoFiles.Scan(path, files, mediaList, subdirs)
  
  # Check for DVD rips.
  paths = path.split('/')
  video_ts = ContainsFile(files, 'video_ts.ifo')
  if video_ts is None:
    video_ts = ContainsFile(files, 'video_ts.bup')
    
  if len(paths) >= 1 and len(paths[0]) > 0 and video_ts is not None:
    print "Found a DVD"
    name = year = None
    
    # Now find the name.
    if paths[-1].lower() == 'video_ts' and len(paths) >= 2:
      # Easiest case.
      (name, year) = VideoFiles.CleanName(paths[-2])
    else:
      # Work up until we find a viable candidate.
      backwardsPaths = paths
      backwardsPaths.reverse()
      for p in backwardsPaths:
        if re.match(nice_match, p):
          (name, year) = VideoFiles.CleanName(p)
          break
          
      if name is None:
        # Use the topmost path.
        (name, year) = VideoFiles.CleanName(paths[0])

    movie = Media.Movie(name, year)
    
    # Add the video_ts file first.
    movie.parts.append(video_ts)

    biggestFile = None
    biggestSize = 0
    
    for i in files:
      if os.path.splitext(i)[1].lower() == '.vob' and os.path.getsize(i) > biggestSize:
        biggestSize = os.path.getsize(i)
        biggestFile = i
       
    # Add the biggest part so that we can get thumbnail/art/analysis from it. 
    if biggestFile is not None:
      movie.parts.append(biggestFile)
        
    if len(movie.parts) > 0:
      mediaList.append(movie)

  # Check for Bluray rips.
  elif len(paths) >= 3 and paths[-1].lower() == 'stream' and paths[-2].lower() == 'bdmv':
    (name, year) = VideoFiles.CleanName(paths[-3])
    movie = Media.Movie(name, year)
    for i in files:
      movie.parts.append(i)
    mediaList.append(movie)
    
  else:
    # Make movies!
    for i in files:
      file = os.path.basename(i)
      (name, year) = VideoFiles.CleanName(os.path.splitext(file)[0])
      
      # If it matches a TV show, don't scan it as a movie.
      tv = False
      for rx in SeriesScanner.episode_regexps[0:-1]:
        if re.match(rx, name):
          print "The file", file, "looked like a TV show so we're skipping it (", rx, ")"
          tv = True
      for rx in SeriesScanner.date_regexps:
        if re.search(rx, file):
          print "The file", file, "looked like a date-based TV show so we're skipping it."
          tv = True

      if tv == False:
        # OK, it's a movie
        movie = Media.Movie(name, year)
        movie.source = VideoFiles.RetrieveSource(file)
        movie.parts.append(i)
        mediaList.append(movie)

    # Stack the results.
    Stack.Scan(path, files, mediaList, subdirs)

    # Clean the folder name and try a match on the folder.
    if len(path) > 0:
      folderName = os.path.basename(path).replace(' ', ' ').replace(' ','.')
      (cleanName, year) = VideoFiles.CleanName(folderName)
      if len(mediaList) == 1 and re.match(nice_match, cleanName):
        res = re.findall(nice_match, cleanName) 
        mediaList[0].name = res[0][0]
        mediaList[0].year = res[0][1]
      elif len(mediaList) == 1 and (len(cleanName) > 1 or year is not None):
        mediaList[0].name = cleanName
        mediaList[0].year = year
      
    if len(mediaList) == 1:
      mediaList[0].guid = checkNfoFile(os.path.dirname(files[0]))
      if mediaList[0].source is None:
        mediaList[0].source = VideoFiles.RetrieveSource(path)
         
  # If the subdirectories indicate that we're inside a DVD, when whack things other than audio and video.
  whack = []
  if 'video_ts' in [s.split('/')[-1].lower() for s in subdirs]:
    for dir in subdirs:
      d = os.path.basename(dir).lower()
      if d not in ['video_ts', 'audio_ts']:
        whack.append(dir)
  
  # Finally, if any of the subdirectories match a TV show, don't enter!
  for dir in subdirs:
    for rx in standalone_tv_regexs:
      res = re.findall(rx, dir)
      if len(res):
        whack.append(dir)
        
  for w in whack:
    subdirs.remove(w)
    
def ContainsFile(files, file):
  for i in files:
    if os.path.basename(i).lower() == file.lower():
      return i
  return None

def checkNfoFile(path):
  try:
    nfoFile=''
    if os.path.exists(path):
      for f in os.listdir(path):
        if f.split(".")[-1].lower() == "nfo":
          nfoFile = os.path.join(path, f)
          t = open(nfoFile)
          nfoText = t.read()
          if nfoText.find('imdb.com') > 0: #imdb.com url, it feels like
            nfoText = nfoText[nfoText.find('imdb.com'):]
            if nfoText.find('/tt') > 0 and nfoText.find('/tt') < 20: #we have a tt url!
              nfoText = nfoText[nfoText.find('/tt'):]
              id = "tt"
              for c in nfoText[3:]:
                try:
                  id += str(int(c))
                except:
                  break
              return id
  except:
    print "Warning, couldn't read NFO file."
