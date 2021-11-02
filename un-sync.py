import filecmp
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

SOURCE_DIR = Path(os.getenv('SOURCE_DIR'))
REPLICA_DIRS = [Path(dir) for dir in os.getenv('REPLICA_DIRS').split(':')]

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

# Ensure `count` replicas of `file_path` exist across all `replica_dirs`.
def ensure_replicas(source_dir, replica_dirs, file_path, count):
  replica_dirs_up_to_date = []
  replica_dirs_outdated = []
  current_count = 0

  for replica_dir in replica_dirs:
    needs_update = False

    if not (replica_dir/file_path).exists():
      needs_update = True
    else:
      diff = filecmp.dircmp(source_dir/file_path, replica_dir/file_path)

      if diff.left_only or diff.right_only or diff.diff_files:
        needs_update = True

    if needs_update:
      replica_dirs_outdated.append(replica_dir)
    else:
      replica_dirs_up_to_date.append(replica_dir)
      current_count += 1

      # File already has the required number of replicas.
      if current_count >= count:
        return

  # Skip missing files.
  if current_count == 0:
    return

  replica_dirs_outdated.sort(key=lambda path: psutil.disk_usage(path).free, reverse=True)

  additional_needed_replicas = count - current_count
  src = replica_dirs_up_to_date[0]/file_path
  for replica_dir_without_file in replica_dirs_outdated[:additional_needed_replicas]:
    dst = replica_dir_without_file/file_path

    print(f"cp -R '{src}' '{dst}'")
    continue

  return

def run(source_dir, replica_dirs):
  for (path, watched) in plex_paths(plex).items():
    if path.is_relative_to(LOCATION_PREFIX):
      relative_path = path.relative_to(LOCATION_PREFIX)
      print(relative_path, watched)

      if not (source_dir/relative_path).exists():
        print(f"Skipping path '{path}'; does not exist in root directory.")
        continue

      replica_count = WATCHED_REPLICAS if watched else UNWATCHED_REPLICAS
      ensure_replicas(source_dir, replica_dirs, relative_path, replica_count)
    else:
      print(f"Skipping path '{path}'; not relative to `LOCATION_PREFIX`.")

if __name__ == '__main__':
  run(SOURCE_DIR, REPLICA_DIRS)
