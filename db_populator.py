import csv
from app import db
from app.models import Movie

# Script to populate db with CSV in the "data" dir.
def populate_db():
    # Open your CSV file
    with open('data/films.csv', 'r') as file:
        csv_reader = csv.DictReader(file)

        # Loop through the rows and insert them into the database
        for row in csv_reader:
            movie = Movie(
                title=row['title'],
                genre=row['genre'],
                year=int(row['year']),
                avg_rating=float(row['avg_rating']),
                description=row['description']  # Add other fields as necessary
            )
            db.session.add(movie)

        # Commit the changes to the database
        db.session.commit()

    print("Database populated with movie data!")

if __name__ == '__main__':
    populate_db()
