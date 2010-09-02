#!/usr/bin/python2.4
import os.path, re, datetime, titlecase, unicodedata

video_exts = ['3gp', 'asf', 'asx', 'avc', 'avi', 'avs', 'bin', 'bivx', 'divx', 'dv', 'dvr-ms', 'evo', 'fli', 'flv', 'ifo', 'img', 
              'iso', 'm2t', 'm2ts', 'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'nrg', 'nsv', 'nuv', 'ogm', 'ogv', 
              'pva', 'qt', 'rm', 'rmvb', 'sdp', 'svq3', 'strm', 'ts', 'ty', 'vdr', 'viv', 'vob', 'vp3', 'wmv', 'wpl', 'xsp', 'xvid']

ignore_files = ['[-\._ ]sample', 'sample[-\._ ]', '-trailer\.']
ignore_dirs =  ['extras?', '!?samples?', 'bonus', '.*bonus disc.*', 'extras?', '\.AppleDouble', '@eaDir']

source_dict = {'bluray':['bdrc','bdrip','bluray','bd','brrip','hdrip','hddvd','hddvdrip'],'cam':['cam'],'dvd':['ddc','dvdrip','dvd','r1','r3'],'retail':['retail'],
               'dtv':['dsr','dsrip','hdtv','pdtv','ppv'],'stv':['stv','tvrip'],'r5':['r5'],'screener':['bdscr','dvdscr','dvdscreener','scr','screener'],
               'svcd':['svcd'],'vcd':['vcd'],'telecine':['tc','telecine'],'telesync':['ts','telesync'],'workprint':['wp','workprint']}
source = []
for d in source_dict:
  for s in source_dict[d]:
    if source != '':
      source.append(s)

audio = ['([^0-9])5\.1[ ]*ch(.)','([^0-9])5\.1([^0-9]?)','([^0-9])7\.1[ ]*ch(.)','([^0-9])7\.1([^0-9])']
subs = ['multi','multisubs']
misc = ['2cd','custom','internal','repack','read.nfo','readnfo','nfofix','proper','rerip','dubbed','subbed','extended','unrated','xxx','nfo','dvxa']
format = ['ac3','dc','divx','fragment','limited','ogg','ogm','ntsc','pal','ps3avchd','r1','r3','r5','720i','720p','1080i','1080p','x264','xvid','vorbis','aac','dts','fs','ws','1920x1080','1280x720','h264']
edition = ['dc','se'] # dc = directors cut, se = special edition
yearRx = '([\(\[\.\-])([1-2][0-9]{3})([\.\-\)\]])'

# Cleanup folder / filenames
def CleanName(name):
  
  orig = name

  # Make sure we pre-compose.
  name = unicodedata.normalize('NFKD', name.decode('utf-8'))
  name = name.lower()

  # grab the year, if there is one. set ourselves up to ignore everything after the year later on.
  year = None
  yearMatch = re.search(yearRx, name)
  if yearMatch:
    yearStr = yearMatch.group(2)
    yearInt = int(yearStr)
    if yearInt > 1900 and yearInt < (datetime.date.today().year + 1):
      year = int(yearStr)
      name = name.replace(yearMatch.group(1) + yearStr + yearMatch.group(3), ' *yearBreak* ')
    
  # Take out things in brackets. (sub acts weird here, so we have to do it a few times)
  done = False
  while done == False:
    (name, count) = re.subn(r'\[[^\]]+\]', '', name, re.IGNORECASE)
    if count == 0:
      done = True
  
  # Take out audio specs, after suffixing with space to simplify rx.
  name = name + ' '
  for s in audio:
    rx = re.compile(s, re.IGNORECASE)
    name = rx.sub('', name)
  
  # Now tokenize.
  tokens = re.split('([^ \-_\.\(\)]+)', name)
  
  # Process tokens.
  newTokens = []
  for t in tokens:
    t = t.strip()
    if not re.match('[\.\-_\(\)]+', t) and len(t) > 0:
    #if t not in ('.', '-', '_', '(', ')') and len(t) > 0:
      newTokens.append(t)

  # Now build a bitmap of good and bad tokens.
  tokenBitmap = []

  garbage = subs
  garbage.extend(misc)
  garbage.extend(format)
  garbage.extend(edition)
  garbage.extend(source)
  garbage.extend(video_exts)
  garbage = set(garbage)
  
  for t in newTokens:
    if t.lower() in garbage:
      tokenBitmap.append(False)
    else:
      tokenBitmap.append(True)
  
  # Now strip out the garbage, with one heuristic; if we encounter 2+ BADs after encountering
  # a GOOD, take out the rest (even if they aren't BAD). Special case for director's cut.
  numGood = 0
  numBad  = 0
  
  finalTokens = []
  
  for i in range(len(tokenBitmap)):
    good = tokenBitmap[i]
    
    # If we've only got one or two tokens, don't whack any, they might be part of
    # the actual name (e.g. "Internal Affairs" "XXX 2")
    #
    if len(tokenBitmap) <= 2:
      good = True
    
    if good and numBad < 2:
      if newTokens[i] == '*yearBreak*':
        #if we have a year, we can ignore everything after this.
        break
      else:
        finalTokens.append(newTokens[i])
    elif not good and newTokens[i].lower() == 'dc':
      finalTokens.append("(Director's cut)")
    
    if good == True:
      numGood += 1
    else:
      numBad += 1
  
  #print "CLEANED [%s] => [%s]" % (orig, u' '.join(finalTokens))
  #print "TOKENS: ", newTokens
  #print "BITMAP: ", tokenBitmap
  #print "FINAL:  ", finalTokens
  
  cleanedName = ' '.join(finalTokens)
  cleanedName = cleanedName.encode('utf-8')
  return (titlecase.titlecase(cleanedName), year)

# Remove files that aren't videos.
def Scan(path, files, mediaList, subdirs):
  filesToRemove = []
  for i in files:
    
    # Broken symlinks and zero byte files need not apply.
    if os.path.exists(i) == False or os.path.getsize(i) == 0:
      filesToRemove.append(i)
      
    else:
      (file, ext) = os.path.splitext(i)
      file = os.path.basename(file)
    
      # Remove files that aren't video.
      if not ext.lower()[1:] in video_exts:
        filesToRemove.append(i)
        
      # Remove hidden files.
      if len(file) == 0 or file[0] == '.':
        filesToRemove.append(i)
    
      # Remove sample files.
      for rx in ignore_files:
        if re.search(rx, i, re.IGNORECASE):
          filesToRemove.append(i)
        
  # Uniquify and remove.
  filesToRemove = list(set(filesToRemove))
  for i in filesToRemove:
    files.remove(i)
      
  # Check directories, but not at the top-level.
  if len(path) > 0:
    whack = []
    for dir in subdirs:
      baseDir = os.path.basename(dir)
      for rx in ignore_dirs:
        if re.match(rx, baseDir, re.IGNORECASE):
          whack.append(dir)
          break
  
    for w in whack:
      subdirs.remove(w)
      
def RetrieveSource(name):
  name = os.path.basename(name)
  wordSplitter = re.compile(r"[^a-zA-Z0-9']+", re.IGNORECASE)
  words = wordSplitter.split(name.upper())
  sources = source
  foundSources = []
  
  # Return the first one we find.
  for d in source_dict:
    for s in source_dict[d]:
      if s.upper() in words:
        return d

# Find the first occurance of a year.
def FindYear(words):
  yearRx = '^[1-2][0-9]{3}$'
  i = 0
  for w in words:
    if re.match(yearRx, w):
      year = int(w)
      if year > 1900 and year < datetime.date.today().year + 1:
        return i
    i += 1
    
  return None
