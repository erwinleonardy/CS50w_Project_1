from src import app, db
from tqdm import tqdm
import csv, psycopg2

def connect(comm):
    if (comm == 'add'):
        addRecords()
    else:
        deleteRecords()

def addRecords():
     with open('books.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for isbn, title, author, yearPublished in tqdm(csv_reader):
            db.execute("INSERT INTO books (isbn, title, author, yearPublished) VALUES (:isbn, :title, :author, :yearPublished)", 
                        {"isbn": isbn, "title": title, "author": author, "yearPublished": yearPublished})
        db.commit()

def deleteRecords():
    db.execute("DELETE FROM books")
    db.commit()

if __name__ == '__main__':
    comm = 'add'
    connect(comm)