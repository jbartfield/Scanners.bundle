# A platform independent way to split paths which might come in with different separators.
def SplitPath(str):
  if str.find('\\') != -1:
    return str.split('\\')
  else:
    return str.split('/')