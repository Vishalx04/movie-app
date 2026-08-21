import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT/"apps"/"api"
sys.path.insert(0, str(API_DIR))

from app.db.database import sessionLocal
from app.db.models import Movie, Genre, MovieStatus

DATA_DIR  = REPO_ROOT/"data"/"ml-20m"
MOVIES_CSV = DATA_DIR/"movies.csv"
LINKS_CSV = DATA_DIR/"links.csv"

TITLE_YEAR_RE = re.compile(r"^(.*)\s\((\d{4})\)\s*$")

def slugify(name:str)->str:
    return name.strip().lower().replace(" ","-").replace("&","and")

def load_links()-> dict[int,str]:
    """movieId and tmdbId mapping"""

    mapping  = {}

    with open(LINKS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tmdb_id  = row.get("tmdbId","").strip()
            if not tmdb_id: 
                continue
            mapping[int(row["movieId"])] = tmdb_id

    return mapping

def parse_title(raw_title:str)->str:
    match = TITLE_YEAR_RE.match(raw_title)
    return match.group(1).strip() if match else raw_title.strip()

def main():
    db  = sessionLocal()

    total = 0
    inserted = 0
    skipped_existing  = 0
    skipped_no_tmdb_id = 0

    try:
        links = load_links()

        existing_movielens_ids = {
            m.movielens_id 
            for m in db.query(Movie.movielens_id).filter(Movie.movielens_id.isnot(None))
        }

        existing_tmdb_ids = {m.tmdb_id for m in db.query(Movie.tmdb_id)}

        genre_cache = {g.name: g for g in db.query(Genre).all()}

        with open(MOVIES_CSV, encoding = "utf-8") as f:
            reader =csv.DictReader(f)

            for row in reader:
                total+=1
                movielens_id = int(row["movieId"])

                if movielens_id in existing_movielens_ids:
                    skipped_existing+=1
                    continue

                tmdb_id = links.get(movielens_id)
                if not tmdb_id:
                    skipped_no_tmdb_id+=1
                    continue

                if tmdb_id in existing_tmdb_ids:
                    skipped_existing+=1
                    continue


                title = parse_title(row["title"])
                genre_names = [
                    g for g in row["genres"].split("|") if g and g != "(no genres listed)"
                ]

                genre_objs = []

                for name in genre_names:
                    if name not in genre_cache:
                        genre = Genre(name = name, slug = slugify(name))
                        db.add(genre)
                        db.flush()
                        genre_cache[name] = genre
                    genre_objs.append(genre_cache[name])

                movie = Movie(
                    tmdb_id  = tmdb_id,
                    movielens_id = movielens_id,
                    title = title,
                    status = MovieStatus.released,
                    adult = False,
                    genres = genre_objs,
                )
                db.add(movie)
                existing_tmdb_ids.add(tmdb_id)
                inserted+=1

                if inserted%500 == 0:
                    db.commit()
                    print(f"  ...{inserted} inserted so far")

        db.commit()

    finally:
        db.close()

    print("\nSeed complete.")
    print(f"  Total rows read:          {total}")
    print(f"  Inserted:                 {inserted}")
    print(f"  Skipped (already exist):  {skipped_existing}")
    print(f"  Skipped (no tmdb_id):     {skipped_no_tmdb_id}")


if __name__ == "__main__":
    main()
