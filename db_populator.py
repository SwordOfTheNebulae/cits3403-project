import csv
from app import app, db
from app.models import Movie

def populate_movies():
    with open("films.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            movie = Movie(
                title=row["title"],
                genre=row["genres"],
                avg_rating=float(row["averageRating"]),
                release_year=int(row["releaseYear"])
            )
            db.session.add(movie)
        db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        populate_movies()
        print("Movies populated successfully!")
