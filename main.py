import logging
import sys
from pathlib import Path

from app.parser import Parser
from app.writers import DumpWriter, TopAlbumsWriter, TopArtistsWriter


def main(args: list[str]) -> int:
    logging.basicConfig(filename="spotify.log", level=logging.INFO)

    force_merge = "--force-merge" in args
    logging.info(f'Force merge enabled "{force_merge}"')

    sourcepath: str = "data"
    outpath: str = "out"
    for arg in args:
        if arg.startswith("--source="):
            idx = arg.index("=") + 1
            sourcepath = arg[idx:]
        elif arg.startswith("--out="):
            idx = arg.index("=") + 1
            outpath = arg[idx:]

    source_dir = Path(sourcepath)

    if not source_dir.exists():
        print('ERROR: Missing input directory "./data"')
        return 1

    parser = Parser()
    parser.add_source_folder(sourcepath)
    parser.add_writers(
        [
            DumpWriter(outpath),
            TopArtistsWriter(outpath),
            TopAlbumsWriter(force_merge, outpath),
        ]
    )

    parser.run_and_save()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
