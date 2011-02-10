#!/usr/bin/env python
import Filter
import os.path

audio_exts = ['mp3', 'm4p', 'm4a', 'm4b', 'flac', 'aac', 'rm', 'rma', 'mpa', 'wav', 'wma', 'ogg', 'mp2', 
              'ac3', 'dts', 'ape', 'mpc', 'mp+', 'mpp', 'shn', 'oga']

# Remove files that aren't audios.
def Scan(path, files, mediaList, subdirs):
  
  # Filter out bad stuff.
  Filter.Scan(path, files, mediaList, subdirs, audio_exts)
