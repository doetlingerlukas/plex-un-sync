# plex-un-sync

Ensure at least *n* copies of unwatched/watched shows exists, either across a MergerFS pool or a manually specified set of directories. Install the [`mergerfs.dup`](https://github.com/trapexit/mergerfs-tools) tool for use with MergerFS for optimized distribution of files.

Since manual copying is done with `rsync`, make sure that all access rights are properly set for all destination directories. The provided Docker image supports remote host destinations with ssh-key authentication.

For usage, have a look at the provided samples, `.en.sample` and `docker-compose.yml.sample`.
