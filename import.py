import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db  = scoped_session(sessionmaker(bind=engine))

def main():
    booksFile = open("books.csv")
    reader = csv.reader(booksFile)

    next(reader, None)
    for isbn, title, author, year in reader:
        print(isbn,title, author, year)
        db.execute("INSERT INTO book (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn,
         "title": title,
          "author": author,
           "year": year})
        
    print("Libros agregados correctamente")
    db.commit()

if __name__ == "__main__":
    main()