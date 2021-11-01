import os

from plexapi.server import PlexServer

plex_url = os.getenv('PLEX_URL')
plex_token = os.getenv('PLEX_TOKEN')

plex = PlexServer(plex_url, plex_token)

for section in plex.library.sections():
  if section.type == 'movie':
    for m in section.searchMovies(unwatched=True):
      print(m.locations)

  if section.type == 'show':
    seasons = section.searchSeasons(unwatched=True)
    for s in seasons:
      for e in s.episodes():
        print(e.locations)
