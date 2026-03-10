from pathlib import Path

from app.parser import Parser
from app.writers import DumpWriter, TopAlbumsWriter, TopArtistsWriter


def main() -> int:
    source_dir = Path("data")

    if not source_dir.exists():
        print('ERROR: Missing input directory "./data"')
        return 1

    parser = Parser()
    parser.add_source_folder("data")
    parser.add_writers([DumpWriter(), TopArtistsWriter(), TopAlbumsWriter()])

    parser.run_and_save()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
