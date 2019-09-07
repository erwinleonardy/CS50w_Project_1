CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR NOT NULL,
  password VARCHAR NOT NULL 
);

CREATE TABLE books (
  isbn VARCHAR PRIMARY KEY,
  title VARCHAR NOT NULL,
  author VARCHAR NOT NULL,
  yearPublished INTEGER NOT NULL
);

CREATE TABLE reviews (
  id INTEGER REFERENCES users(id),
  username VARCHAR NOT NULL,
  isbn VARCHAR REFERENCES books(isbn),
  star DECIMAL NOT NULL,
  review VARCHAR NOT NULL,
  review_timestamp TIMESTAMP NOT NULL,
  PRIMARY KEY (id, isbn)
);