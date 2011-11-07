import os, re

IGNORE_DIRS = ['@eaDir', '.*_UNPACK_.*', '.*_FAILED_.*', '\..*', 'lost\+found']
ROOT_IGNORE_DIRS = ['\$Recycle.Bin', 'System Volume Information']

# Remove files and directories that don't make sense to scan.
def Scan(path, files, mediaList, subdirs, exts):

  files_to_whack = []
  use_unicode = os.path.supports_unicode_filenames

  for i in files:
    # Only use unicode if it's supported, which it is on Windows and OS X,
    # but not Linux. This allows things to work with non-ASCII characters
    # without having to go through a bunch of work to ensure the Linux 
    # filesystem is UTF-8 "clean".
    #
    if use_unicode:
      try: filename = unicode(i.decode('utf-8'))
      except: files_to_whack.append(i)
    else:
      filename = i
      
    (file, ext) = os.path.splitext(i)
    file = os.path.basename(file)
    
    # If extension is wrong, don't include.
    if not ext.lower()[1:] in exts:
      files_to_whack.append(i)
    
    # Broken symlinks and zero byte files need not apply.
    if os.path.exists(filename) == False or os.path.getsize(filename) == 0:
      files_to_whack.append(i)
      
    # Remove hidden files.
    if len(file) == 0 or file[0] == '.':
      files_to_whack.append(i)

  # Whack files.
  files_to_whack = list(set(files_to_whack))
  for i in files_to_whack:
    files.remove(i)

  # See what directories to ignore.
  ignore_dirs_total = IGNORE_DIRS
  if len(path) == 0:
    ignore_dirs_total += ROOT_IGNORE_DIRS

  dirs_to_whack = []
  for dir in subdirs:
    # See which directories to get rid of.
    baseDir = os.path.basename(dir)
    for rx in ignore_dirs_total:
      if re.match(rx, baseDir, re.IGNORECASE):
        dirs_to_whack.append(dir)
        break
  
  # Remove the directories.
  dirs_to_whack = list(set(dirs_to_whack))
  for i in dirs_to_whack:
    subdirs.remove(i)
