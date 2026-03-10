__all__ = ["Writer", "DumpWriter", "TopArtistsWriter", "TopAlbumsWriter"]

import json
from abc import ABC
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import OrderedDict

from app.models import Artist


def serialize_datetime(obj: datetime) -> str:
    if not isinstance(obj, datetime):
        raise TypeError(
            "Unexpected type when attempting to serialize datetime"
        )

    return obj.isoformat()


class Writer(ABC):
    __slots__ = "name"
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

        Path("out").mkdir(exist_ok=True)

    def get_outpath(self) -> Path:
        return Path(f"out/{self.name}.json")

    def write(self, data: dict[str, Artist]) -> None: ...


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
                default=serialize_datetime,
            )
        )


class TopArtistsWriter(Writer):
    def __init__(self) -> None:
        Writer.__init__(self, "top-artists")

    def write(self, data: dict[str, Artist]) -> None:
        artist_data = OrderedDict(
            map(
                lambda row: (row[0], row[1].total_listens),
                sorted(
                    data.items(),
                    key=lambda row: row[1].total_listens,
                    reverse=True,
                ),
            )
        )

        outfile = self.get_outpath()
        outfile.write_text(json.dumps(artist_data, indent=4))


class TopAlbumsWriter(Writer):
    force_merge: bool = False
    first: bool = True

    def __init__(self, force_merge: bool) -> None:
        Writer.__init__(self, "top-albums")
        self.force_merge = force_merge

    def __get_album_mappings(self, artist: Artist) -> dict[str, list[str]]:
        album_names = list(artist.albums.keys())
        mapped_albums: list[str] = []
        mappings: dict[str, list[str]] = {}

        for album in sorted(album_names, key=len):
            if album in mapped_albums:
                continue

            similar_names = []

            for other in album_names:
                if other == album:
                    continue

                if other.startswith(album):
                    similar_names.append(other)

            if not similar_names:
                mapped_albums.append(album)
                mappings[album] = [album]
                continue

            if not self.force_merge:
                if self.first:
                    self.first = False
                    print()

                combine = input(
                    f"Found {len(similar_names)} albums like {album}.\n"
                    + f"{','.join(similar_names)}\n"
                    + "Join albums into single entry? [Y/n]: "
                )

                if combine.startswith("n"):
                    continue

            mappings[album] = [album, *similar_names]
            mapped_albums.extend([album, *similar_names])

        return mappings

    def write(self, data: dict[str, Artist]) -> None:
        album_data = {}

        for artist_name, artist in data.items():
            mapped_albums = self.__get_album_mappings(artist)

            for parent, children in mapped_albums.items():
                listen_data = {
                    "total_listens": 0,
                }

                for child in children:
                    child_data = artist.albums.get(child)
                    if child_data is None:
                        raise ValueError(f"Expected album data for {child}")

                    listen_data[child] = child_data.total_listens
                    listen_data["total_listens"] += child_data.total_listens

                album_data[f"{artist_name} <:> {parent}"] = listen_data

        output = OrderedDict(
            sorted(
                album_data.items(),
                key=lambda kvp: kvp[1]["total_listens"],
                reverse=True,
            )
        )

        outfile = self.get_outpath()
        outfile.write_text(json.dumps(output, indent=4))
