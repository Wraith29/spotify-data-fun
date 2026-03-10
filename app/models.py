__all__ = ["Row", "Entry", "Album", "Artist", "row_to_entry"]

from datetime import datetime
from dataclasses import dataclass, field
from typing import TypedDict


class Row(TypedDict):
    ts: str | None
    master_metadata_album_artist_name: str | None
    master_metadata_album_album_name: str | None
    master_metadata_track_name: str | None


@dataclass
class Entry:
    timestamp: datetime
    artist_name: str
    album_name: str
    track_name: str


def row_to_entry(row: Row) -> Entry | None:
    timestamp = row["ts"]
    if timestamp is None:
        return None

    artist_name = row["master_metadata_album_artist_name"]
    if artist_name is None:
        return None

    album_name = row["master_metadata_album_album_name"]
    if album_name is None:
        return None

    track_name = row["master_metadata_track_name"]
    if track_name is None:
        return None

    parsed_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

    return Entry(parsed_time, artist_name, album_name, track_name)


@dataclass(slots=True)
class Track:
    total_listens: int = 0
    first_listen: datetime = field(default=datetime.max)
    latest_listen: datetime = field(default=datetime.min)

    def update(self, entry: Entry) -> None:
        self.total_listens += 1

        self.first_listen = min(self.first_listen, entry.timestamp)
        self.latest_listen = max(self.latest_listen, entry.timestamp)


@dataclass(slots=True)
class Album:
    tracks: dict[str, Track] = field(default_factory=dict)
    total_listens: int = 0
    first_listen: datetime = field(default=datetime.max)
    latest_listen: datetime = field(default=datetime.min)

    def update(self, entry: Entry) -> None:
        self.total_listens += 1
        self.first_listen = min(self.first_listen, entry.timestamp)
        self.latest_listen = max(self.latest_listen, entry.timestamp)

        track = self.tracks.get(entry.track_name, Track())
        track.update(entry)
        self.tracks[entry.track_name] = track


@dataclass(slots=True)
class Artist:
    albums: dict[str, Album] = field(default_factory=dict)
    total_listens: int = 0
    first_listen: datetime = field(default=datetime.max)
    latest_listen: datetime = field(default=datetime.min)

    def update(self, entry: Entry) -> None:
        self.total_listens += 1
        self.first_listen = min(self.first_listen, entry.timestamp)
        self.latest_listen = max(self.latest_listen, entry.timestamp)

        album = self.albums.get(entry.album_name, Album())
        album.update(entry)
        self.albums[entry.album_name] = album
