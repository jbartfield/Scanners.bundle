#!/usr/bin/env python
import os.path

audio_exts = ['.mp3', '.m4p', '.m4a', '.m4b', '.flac', '.aac', '.rm', '.rma', '.mpa', '.wav', '.wma', '.ogg', '.mp2', 
              '.ac3', '.dts', '.ape', '.mpc', '.mp+', '.mpp', '.shn', '.oga']

# Remove files that aren't audios.
def Scan(path, files, mediaList, subdirs):
  filesToRemove = []
  for i in files:

    # Broken symlinks and zero byte files need not apply.
    if os.path.exists(i) == False or os.path.getsize(i) == 0:
      filesToRemove.append(i)

    else:
      (file, ext) = os.path.splitext(i)
      file = os.path.basename(file)

      # Remove files that aren't audio.
      if not ext.lower() in audio_exts:
        filesToRemove.append(i)

      # Remove hidden files.
      elif len(file) == 0 or file[0] == '.':
        filesToRemove.append(i)

  for i in filesToRemove:
    files.remove(i) 

