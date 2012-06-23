class MediaRoot:
  def __init__(self, type):
    self.name = ''
    self.year = None
    self.type = type
    self.parts = []
    self.subtitles = []
    self.thumbs = []
    self.arts = []
    self.trailers = []
    self.released_at = None
    self.display_offset = 0
    self.source = None
    self.themes = []
    
class Movie(MediaRoot):
  def __init__(self, name, year=None):
    MediaRoot.__init__(self,'Movie')
    self.name = name
    self.year = year
    self.guid = None
    
  def __repr__(self):
    if self.year is not None:
      return "%s (%s)" % (self.name, self.year)
    else:
      return "%s" % (self.name)

class Episode(MediaRoot):
  def __init__(self, show, season, episode, title=None, year=None):
    MediaRoot.__init__(self, 'Episode')
    self.show = show
    self.season = season
    self.episode = episode
    self.name = title
    self.year = year
    self.episodic = True
    
  def __repr__(self):
    return "%s (season %s, episode: %s) => %s starting at %d" % (self.show, self.season, self.episode, self.parts, self.display_offset)
    
class Track(MediaRoot):
  def __init__(self, artist, album, title=None, index=None, year=None, disc=None, album_artist=None):
    MediaRoot.__init__(self, 'Track')
    self.artist = artist
    self.album = album
    self.name = title
    self.index = index
    self.year = year
    self.disc = disc
    self.album_artist = album_artist
    self.title = ''
    
  def __repr__(self):
    return "%s (album: %s, track: %s) #%d => %s" % (self.artist, self.album, self.name, self.index, self.title)
    
class Photo(MediaRoot):
  def __init__(self, title):
    MediaRoot.__init__(self, 'Photo')
    self.name = title
