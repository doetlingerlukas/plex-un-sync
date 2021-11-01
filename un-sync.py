import config
from plexapi.server import PlexServer

plex = PlexServer(config.plex_url, config.token)
