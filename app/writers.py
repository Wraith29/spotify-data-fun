__all__ = ["Writer", "DumpWriter", "TopArtistsWriter", "TopAlbumsWriter"]

import json
from abc import ABC
from dataclasses import asdict
from operator import itemgetter
from pathlib import Path
from typing import OrderedDict
from datetime import datetime

from app.models import Artist


def serialize_datetime(obj: datetime) -> str:
    if not isinstance(obj, datetime):
        raise TypeError("Fuck off")

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
    def __init__(self) -> None:
        Writer.__init__(self, "top-albums")

    def write(self, data: dict[str, Artist]) -> None:
        album_data: dict[str, int] = {}

        for artist_name, artist in data.items():
            for album_name, album in artist.albums.items():
                album_data[f"{artist_name} - {album_name}"] = (
                    album.total_listens
                )

        output = OrderedDict(
            sorted(album_data.items(), key=itemgetter(1), reverse=True)
        )

        outfile = self.get_outpath()
        outfile.write_text(json.dumps(output, indent=4))
