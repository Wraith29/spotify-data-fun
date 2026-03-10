import json
import shutil
import time
from abc import ABC
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from operator import itemgetter
from pathlib import Path
from typing import TypedDict


def term_width() -> int:
    return shutil.get_terminal_size((100, 100)).columns


class LogEntry(TypedDict):
    master_metadata_album_artist_name: str | None
    master_metadata_album_album_name: str | None
    master_metadata_track_name: str | None


@dataclass
class Entry:
    artist_name: str
    album_name: str
    track_name: str


def to_entry(log_entry: LogEntry) -> Entry | None:
    artist_name = log_entry["master_metadata_album_artist_name"]
    if artist_name is None:
        return None

    album_name = log_entry["master_metadata_album_album_name"]
    if album_name is None:
        return None

    track_name = log_entry["master_metadata_track_name"]
    if track_name is None:
        return None

    return Entry(artist_name, album_name, track_name)


@dataclass(slots=True)
class Album:
    tracks: dict[str, int] = field(default_factory=dict)
    total_listens: int = 0

    def update(self, entry: Entry) -> None:
        self.total_listens += 1

        track = self.tracks.get(entry.track_name, 0)
        track += 1
        self.tracks[entry.track_name] = track


@dataclass(slots=True)
class Artist:
    albums: dict[str, Album] = field(default_factory=dict)
    total_listens: int = 0

    def update(self, entry: Entry) -> None:
        self.total_listens += 1

        album = self.albums.get(entry.album_name, Album())
        album.update(entry)
        self.albums[entry.album_name] = album


class Writer(ABC):
    __slots__ = "name"
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

        Path("out").mkdir(exist_ok=True)

    def get_outpath(self) -> Path:
        return Path(f"out/{self.name}.json")

    def write(self, data: dict[str, Artist]) -> None: ...


class Parser:
    min_width: int
    current: int
    data: dict[str, Artist] = {}
    writers: list[Writer] = []

    def __init__(self) -> None:
        self.current = 1
        self.min_width = term_width()

    def add_writer(self, writer: Writer) -> None:
        self.writers.append(writer)

    def add_source(self, fp: str, total: int) -> None:
        print(
            f"[{self.current}/{total}] Parsing {fp}".ljust(
                self.min_width, " "
            ),
            end="\r",
        )

        src = Path(fp).read_text()
        obj = list(json.loads(src))

        log: LogEntry
        for log in obj:
            entry = to_entry(log)
            if entry is None:
                continue

            artist = self.data.get(entry.artist_name, Artist())
            artist.update(entry)
            self.data[entry.artist_name] = artist

        self.current += 1

    def add_sources(self, files: list[str]) -> None:
        for file in files:
            self.add_source(file, len(files))
        print()

    def write_all(self) -> None:
        current = 1
        total = len(self.writers)

        for writer in self.writers:
            print(
                f"[{current}/{total}] Executing writer ({writer.name})".ljust(
                    self.min_width, " "
                ),
                end="\r",
            )
            writer.write(self.data)
            current += 1

            time.sleep(1)
        print()


class DumpWriter(Writer):
    def __init__(self) -> None:
        Writer.__init__(self, "dump")

    def write(self, data: dict[str, Artist]) -> None:
        output = OrderedDict(
            map(
                lambda kvp: (kvp[0], asdict(kvp[1])),
                sorted(
                    data.items(),
                    key=lambda kvp: kvp[1].total_listens,
                    reverse=True,
                ),
            )
        )

        outfile = self.get_outpath()
        outfile.write_text(
            json.dumps(
                output,
                indent=4,
            )
        )


class TopAlbumsWriter(Writer):
    def __init__(self) -> None:
        Writer.__init__(self, "top-albums")

    def write(self, data: dict[str, Artist]) -> None:
        album_data: dict[str, int] = {}

        for artist in data.values():
            for album_name, album in artist.albums.items():
                album_data[album_name] = album.total_listens

        output = OrderedDict(
            sorted(album_data.items(), key=itemgetter(1), reverse=True)
        )

        outfile = self.get_outpath()
        outfile.write_text(json.dumps(output, indent=4))


def main() -> int:
    if not Path("data").exists():
        print('ERROR: Missing input directory "./data"')
        return 1

    files_to_parse = [
        str(sub.absolute()) for sub in Path("data").iterdir() if sub.is_file()
    ]

    parser = Parser()
    parser.add_writer(DumpWriter())
    parser.add_writer(TopAlbumsWriter())

    parser.add_sources(files_to_parse)

    parser.write_all()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
