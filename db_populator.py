import csv
from app import app, db
from app.models import Movie

def populate_movies():
    with open("data/films.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        already_seen = set()
        for row in reader:
            title = row["title"]
            year = int(row["release_year"])
            if((title,year) in already_seen): continue # skip duplicates
            already_seen.add((title,year))
            movie = Movie(
                title=title,
                genre=row["genre"],
                avg_rating=float(row["avg_rating"]),
                release_year=year
            )
            db.session.add(movie)
        db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        populate_movies()
        print("Movies populated successfully!")
