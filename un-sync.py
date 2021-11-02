import os
from pathlib import Path

from plexapi.server import PlexServer
import psutil

plex_url = os.getenv('PLEX_URL')
plex_token = os.getenv('PLEX_TOKEN')

plex = PlexServer(plex_url, plex_token)

unwatched_replicas = 2
watched_replicas = 1

WATCHED_REPLICAS = int(os.getenv('WATCHED_REPLICAS', '1'))
UNWATCHED_REPLICAS = int(os.getenv('UNWATCHED_REPLICAS', '2'))
LOCATION_PREFIX = Path(os.getenv('LOCATION_PREFIX', ''))

# Get a dictionary containing all movie and season paths and their watched status.
def plex_paths(plex):
  paths = {}

  for section in plex.library.sections():
    if section.type == 'movie':
      for movie in section.searchMovies():
        for movie_location in movie.locations:
          movie_location = Path(movie_location)
          paths[movie_location] = movie.isWatched
    elif section.type == 'show':
      for season in section.searchSeasons():
        for show_location in season.show().locations:
          show_location = Path(show_location)
          season_location = show_location/season.title
          paths[season_location] = season.isWatched
    else:
      continue

  return paths

# Ensure `count` replicas of `file_path` exist across all `replica_root_paths`.
def ensure_replicas(replica_root_paths, file_path, count):
  replica_root_paths_with_file = []
  replica_root_paths_without_file = []
  current_count = 0

  for replica_root_path in replica_root_paths:
    if replica_root_path.join(file_path).exists():
      replica_root_paths_with_file.push(replica_root_path)
      current_count += 1

      # File already has the required number of replicas.
      if current_count >= count:
        return
    else:
      replica_root_paths_without_file.push(replica_root_path)

  # Skip missing files.
  if current_count == 0:
    return

  replica_root_paths_without_file.sort(key=lambda path: psutil.disk_usage(path).free, reverse=True)

  additional_needed_replicas = count - current_count
  src = replica_root_paths_with_file[0]/file_path
  for replica_root_path_without_file in replica_root_paths_without_file[..additional_needed_replicas]:
    dst = replica_root_path_without_file/file_path

    print(f"cp '{src}' '{dst}'")
    continue

  return

for (path, watched) in plex_paths(plex).items():
  if path.is_relative_to(LOCATION_PREFIX):
    relative_path = path.relative_to(LOCATION_PREFIX)
    print(relative_path, watched)

    root_paths = []
    replica_count = WATCHED_REPLICAS if watched else UNWATCHED_REPLICAS
    ensure_replicas(root_paths, relative_path, replica_count)
  else:
    print(f"Skipping path '{path}'.")
