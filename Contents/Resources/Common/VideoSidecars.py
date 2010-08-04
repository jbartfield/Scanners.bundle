import Media, VideoFiles
import os.path, re

def FindSiblingFiles(mediaItem, exts, list, suffix=''):
  #print mediaItem.parts
  pass

def Scan(dir, files, mediaList, subdirs):

  for mediaItem in mediaList:

    # Subtitles.
    FindSiblingFiles(mediaItem, ['.srt', 'smi', 'sub', 'ass', 'ssa'], mediaItem.subtitles)

    # Thumbs, art.
    FindSiblingFiles(mediaItem, ['.png', '.jpg', '.tbn'], mediaItem.thumbs)
    FindSiblingFiles(mediaItem, ['.png', '.jpg', '.tbn'], mediaItem.arts, '-fanart')
    
    # Trailers.
    FindSiblingFiles(mediaItem, VideoFiles.video_exts, mediaItem.trailers, '-trailer')