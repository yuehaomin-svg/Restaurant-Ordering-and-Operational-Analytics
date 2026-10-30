import zipfile
from pathlib import Path
from urllib.request import urlretrieve


DATASET_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_path = raw_dir / "online_retail_ii.zip"
    urlretrieve(DATASET_URL, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(raw_dir)
    files = [path.name for path in raw_dir.iterdir() if path.is_file()]
    print(f"Downloaded UCI Online Retail II to {raw_dir}")
    print("\n".join(sorted(files)))


if __name__ == "__main__":
    main()
