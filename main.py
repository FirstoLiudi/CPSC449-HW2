# pip install fastapi uvicorn pydantic sqlalchemy mysqlclient
from fastapi import FastAPI, HTTPException, Depends  # Import FastAPI and related modules.
from pydantic import BaseModel  # Import Pydantic BaseModel
from typing import List  # Import List for type hinting.
from sqlalchemy import create_engine, Column, Integer, String  # SQLAlchemy utilities for ORM mapping.
from sqlalchemy.ext.declarative import declarative_base  # Base class for SQLAlchemy models.
from sqlalchemy.orm import sessionmaker, Session  # Session and sessionmaker for database operations.

DATABASE_URL = "mysql://root:abc123@localhost/book_management_1" # Database connection string for SQLAlchemy configuration

engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})  # SQLAlchemy engine with charset.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Session factory for managing DB sessions.

def get_db(): # Dependency to get the DB session. Ensures proper session handling with context management.
    db = SessionLocal()  # Create a new session.
    try:
        yield db  # Yield the session to the endpoint function.
    finally:
        db.close()  # Ensure the session is closed after the request.

Base = declarative_base()  # Base class for defining SQLAlchemy models.

class Book(Base): # Data Model for a Book (SQLAlchemy) representing the 'books' table in the database.
    __tablename__ = "books"  # Table name in the database.
    id = Column(Integer, primary_key=True, index=True)  # Primary key column with an index.
    title = Column(String(255), nullable=False)  # Title column, cannot be null.
    author = Column(String(255), nullable=False)  # Author column, cannot be null.

Base.metadata.create_all(bind=engine)  # Create the tables in the database (doesn't do anything if already exist)

class BookCreate(BaseModel): # Data model for a Book (Pydantic) for validating input data when creating or updating books.
    title: str  # Title field.
    author: str  # Author field.

class BookOut(BookCreate): # Data model for a Book (Pydantic) for validating output data when returning book information (inherits the input, but with id).
    id: int  # Book ID field.

    class Config:
        orm_mode = True  # Enable automatic conversion of ORM objects to dict.

app = FastAPI()  # FastAPI application instance.

@app.get("/books", response_model=List[BookOut]) # Route for getting all books, returns a list of books (formatted according to the BookOut schema)
def get_books(db: Session = Depends(get_db)): # The function for the GET /books route
    books = db.query(Book).all()  # Fetch all books from the database.
    return books  # Return the list of books.

@app.get("/books/{book_id}", response_model=BookOut) # Route for getting a specific books with the id in the path, returns the single books (formatted according to the BookOut schema)
def get_book(book_id: int, db: Session = Depends(get_db)): # The function for the GET /books/{book_id} route, where 'book_id' parameter is taken from the URL path and automatically converted to an integer
    book = db.query(Book).filter(Book.id == book_id).first()  # Query the book by ID.
    if not book:  # If no book is found, raise a 404 error.
        raise HTTPException(status_code=404, detail="Book not found") # Raise the 404 error, indicating the book doesn't exist
    return book  # Return the book data.

@app.post("/books", response_model=BookOut) # Route for creating a new book, returns the created book (formatted according to the BookOut schema)
def create_book(book: BookCreate, db: Session = Depends(get_db)): # The function for the POST /books route, where 'book' is parsed from the request body to a BookCreate object
    db_book = Book( # The book to be added to the books table
        title=book.title,  # Set the book's title.
        author=book.author,  # Set the book's author.
    )
    db.add(db_book)  # Add the new book to the session.
    db.commit()  # Commit the session to save the book to the database.
    db.refresh(db_book)  # Refresh the instance to get the updated data.
    return db_book  # Return the created book.

@app.put("/books/{book_id}", response_model=BookOut) # Route for editing info of an existing book with the id in the path, returns the updated book (formatted according to the BookOut schema)
def update_book(book_id: int, updated_book: BookCreate, db: Session = Depends(get_db)): # The function for the PUT /book/{book_id} route, where 'updated_book' is parsed from the request body to a BookCreate object
    db_book = db.query(Book).filter(Book.id == book_id).first()  # Query the book by ID.
    if not db_book:  # If no book is found, raise a 404 error.
        raise HTTPException(status_code=404, detail="Book not found") # Raise the 404 error, indicating the book doesn't exist
    
    db_book.title = updated_book.title  # Update the book's title.
    db_book.author = updated_book.author  # Update the book's author.
    
    db.commit()  # Commit the session to save the changes.
    db.refresh(db_book)  # Refresh the instance to get the updated data.
    return db_book  # Return the updated book.

@app.delete("/books/{book_id}") # Route for deleting a book with the id in the path
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()  # Query the book by ID.
    if not db_book:  # If no book is found, raise a 404 error.
        raise HTTPException(status_code=404, detail="Book not found") # Raise the 404 error, indicating the book doesn't exist
    
    db.delete(db_book)  # Delete the book from the session.
    db.commit()  # Commit the session to apply the deletion.
    return {"message": f"Book(id={book_id}) deleted succesfully"}  # Return a success message.