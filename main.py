import logging
import sys
from pathlib import Path

from app.parser import Parser
from app.writers import DumpWriter, TopAlbumsWriter, TopArtistsWriter


def main(args: list[str]) -> int:
    logging.basicConfig(filename="spotify.log", level=logging.INFO)

    force_merge = "--force-merge" in args
    logging.info(f'Force merge enabled "{force_merge}"')

    source_dir = Path("data")

    if not source_dir.exists():
        print('ERROR: Missing input directory "./data"')
        return 1

    parser = Parser()
    parser.add_source_folder("data")
    parser.add_writers(
        [DumpWriter(), TopArtistsWriter(), TopAlbumsWriter(force_merge)]
    )

    parser.run_and_save()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
