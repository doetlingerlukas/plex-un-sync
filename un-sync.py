import filecmp
import os
import sys
import importlib
from pathlib import Path
from shutil import which
from plexapi.server import PlexServer
import subprocess
import shlex
import psutil
import re

plex_url = os.getenv('PLEX_URL')
plex_token = os.getenv('PLEX_TOKEN')

plex = PlexServer(plex_url, plex_token)

WATCHED_REPLICAS = int(os.getenv('WATCHED_REPLICAS', '1'))
UNWATCHED_REPLICAS = int(os.getenv('UNWATCHED_REPLICAS', '2'))
LOCATION_PREFIX = Path(os.getenv('LOCATION_PREFIX'))

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

def execute_cmd(args):
  return subprocess.call(args)

def print_args(args):
  quoted = [shlex.quote(arg) for arg in args]
  print(' '.join(quoted))

def is_remote_replica(replica_dir):
  return re.match('[^\s]+@.*', str(replica_dir))

def replica_exists(replica_dir, relative_path):
  if is_remote_replica(replica_dir):
    host = str(replica_dir).split(':')

    status = execute_cmd(['ssh', host[0], f"test -f {shlex.quote(str(Path(host[1])/relative_path))}"])
    if status == 0:
      return True
    elif status == 1:
      return False
    else:
      raise Exception(f"ssh failed with status {status}")
  else:
    return (replica_dir/relative_path).exists()

def replica_dir_size(replica_dir):
  if is_remote_replica(replica_dir):
    host = str(replica_dir).split(':')

    result = subprocess.run(['ssh', host[0], f"df --output=avail {host[1]}"], stdout = subprocess.PIPE)
    search = re.search('(.*)([0-9+])(.*)', result.stdout.decode('utf-8'))
    result_str = search.group(1) if search else '0'
    print(result_str)
    return int(result_str)
  else:
    return psutil.disk_usage(replica_dir).free

# Ensure `count` replicas of `relative_path` exist across all `replica_dirs`.
def ensure_replicas(source_dir, replica_dirs, relative_path, count, dry_run):
  used_replica_dirs = []
  unused_replica_dirs = []

  # Skip if replica not required
  if count <= 1:
    return

  for replica_dir in replica_dirs:
    if replica_exists(replica_dir, relative_path):
      used_replica_dirs.append(replica_dir)
    else:
      unused_replica_dirs.append(replica_dir)

  used_replica_dirs.sort(key=lambda path: replica_dir_size(path), reverse=True)
  unused_replica_dirs.sort(key=lambda path: replica_dir_size(path), reverse=True)

  replica_dirs_to_update = []
  replica_dirs_to_delete = []

  if count < len(used_replica_dirs):
    diff = len(used_replica_dirs) - count
    replica_dirs_to_delete.extend(used_replica_dirs[:diff])
    replica_dirs_to_update.delete(used_replica_dirs[diff:])
  else:
    replica_dirs_to_update.extend(used_replica_dirs)
    additional_needed_replicas = count - len(used_replica_dirs)
    replica_dirs_to_update.extend(unused_replica_dirs[:additional_needed_replicas])


  src = source_dir/relative_path
  for replica_dir in replica_dirs_to_update:
    dst = f"{replica_dir}/"

    args = ['rsync', '-avHAXWE', '--numeric-ids', '--progress', '--relative', str(src), str(dst)]

    print_args(args)
    if not dry_run:
      execute_cmd(args)
    continue

  for replica_dir in replica_dirs_to_delete:
    dst = replica_dir/relative_path
    print(f"Replica {dst} is unused and should be deleted.")

  return

mergerfs_dup_path = which('mergerfs.dup')
if mergerfs_dup_path:
  module_name = 'mergerfs_dup'
  spec = importlib.util.spec_from_loader(
    module_name,
    importlib.machinery.SourceFileLoader(module_name, mergerfs_dup_path)
  )
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  sys.modules[module_name] = module
  from mergerfs_dup import ismergerfs
else:
  def ismergerfs(dir):
    return False

def main():
  dry_run = os.getenv('DRY_RUN', 'false') == 'true'

  source_dir_raw = os.path.realpath(os.getenv('SOURCE_DIR'))
  source_dir = Path(source_dir_raw)

  use_mergerfs_dup = False
  replica_dirs = None
  if ismergerfs(source_dir_raw):
    use_mergerfs_dup = True
  else:
    replica_dirs = [Path(dir) for dir in os.getenv('REPLICA_DIRS').split(';')]

  for (path, watched) in plex_paths(plex).items():
    if LOCATION_PREFIX and path.is_relative_to(LOCATION_PREFIX):
      relative_path = path.relative_to(LOCATION_PREFIX)
      # print(relative_path, watched)

      if not (source_dir/relative_path).exists():
        print(f"Skipping path '{path}'; does not exist in root directory.")
        continue

      replica_count = WATCHED_REPLICAS if watched else UNWATCHED_REPLICAS

      if use_mergerfs_dup:
        execute = [] if dry_run else ['--execute']
        execute_cmd([mergerfs_dup_path, '--count', str(replica_count), source_dir/relative_path] + execute)
      else:
        ensure_replicas(source_dir, replica_dirs, relative_path, replica_count, dry_run)
    else:
      # print(f"Skipping path '{path}'; not relative to `LOCATION_PREFIX`.")
      pass

if __name__ == '__main__':
  main()
