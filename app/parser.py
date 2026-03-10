__all__ = ["Parser"]

import json
import logging
import shutil
from pathlib import Path
from timeit import default_timer as timestamp

from app.models import Artist, Entry, Row, row_to_entry
from app.writers import Writer


def term_width() -> int:
    return shutil.get_terminal_size((100, 100)).columns


class Parser:
    min_width: int
    current: int
    sources: list[str] = []
    data: dict[str, Artist] = {}
    writers: list[Writer] = []

    def __init__(self) -> None:
        self.current = 1
        self.min_width = term_width()

    def add_writer(self, writer: Writer) -> None:
        self.writers.append(writer)

    def add_writers(self, writers: list[Writer]) -> None:
        for writer in writers:
            logging.info(f'Adding writer "{writer.name}"')

        self.writers.extend(writers)

    def add_source_folder(self, name: str) -> None:
        logging.info(f'Adding source folder "{name}"')

        source_dir = Path(name)
        self.sources = [
            str(sub.absolute())
            for sub in source_dir.iterdir()
            if sub.is_file()
        ]

    def parse_source(self, name: str) -> None:
        logging.info(f'Processing "{name}"')
        print(
            f"[{self.current}/{len(self.sources)}] Processing {name}".ljust(
                self.min_width, " "
            ),
            end="\r",
        )

        src = Path(name).read_text()
        obj = list(json.loads(src))

        row: Row
        entry: Entry | None
        for row in obj:
            entry = row_to_entry(row)
            if entry is None:
                continue

            artist = self.data.get(entry.artist_name, Artist())
            artist.update(entry)
            self.data[entry.artist_name] = artist

        self.current += 1

        logging.info(f'Completed processing "{name}"')

    def parse(self) -> None:
        logging.info("Beginning processing")
        start = timestamp()
        for source in self.sources:
            self.parse_source(source)
        logging.info("Completed processing")
        print()
        end = timestamp()

        print(f"Processing Sources completed in {end - start:.2f}s")

    def write(self) -> None:
        start = timestamp()
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
        print()

        end = timestamp()
        print(f"Executing Writers completed in {end - start:.2f}s")

    def run_and_save(self) -> None:
        self.parse()
        self.write()
