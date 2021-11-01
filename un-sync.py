import os

from plexapi.server import PlexServer

plex_url = os.getenv('PLEX_URL')
plex_token = os.getenv('PLEX_TOKEN')

plex = PlexServer(plex_url, plex_token)
