import os
import Filter, Media

photo_exts = ['png','jpg','jpeg','bmp','gif','ico','tif','tiff','tga','pcx','dng','nef','cr2','crw','orf','arw','erf','3fr','dcr','x3f','mef','raf','mrw','pef','sr2']

# Scans through files, and add to the media list.
def Scan(path, files, mediaList, subdirs, language=None, **kwargs):
  
  # Filter out bad stuff.
  Filter.Scan(path, files, mediaList, subdirs, photo_exts)
  
  # Add all the photos to the list.
  for path in files:
    file = os.path.basename(path)
    title,ext = os.path.splitext(file)
    photo = Media.Photo(title)
    photo.parts.append(path)
    mediaList.append(photo)