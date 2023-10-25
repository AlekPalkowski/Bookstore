# Program for book keeping to create a database to store, update books, and search for books. 
# This program displays results of authors when similar titles are present and gives suggestions if mispelt titles are given
import sqlite3
# This is for similar searches. You can use fuzzywuzzy but that requires to install libraries
import difflib

"""
Changes made:
    rollback added to functions that will change the database (add_book, update_book, delete_book)
    created a table on start up with pre-generated books (def populate_table)
        - added a few titles to show the code work with different titles but same author and same author but different titles
    also added more function to the delete menu option. Also included deleting by the books ID which then gives a confirmation of the book and title to delete
"""

class BookDatabase:
    def __init__(self, database_name):
        """
        Initialize a BookDatabase object by connecting it to the SQLite database.
        
        Arguements:
            database_name (string). This is the name of the SQLite database to connect to.
        """
        try:
            self.conn = sqlite3.connect(database_name)
            self.create_table()
        except sqlite3.Error as e:
            print(f'Error accessing the database: {e}')
            raise
    
    def populate_table(self):
        """
        Creates a table at start up (if none) and inserts the required 5 books with their details.
        Make sure there isnt a table that already exists
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type ='table'")
            table_already_exists = cursor.fetchone()

            if not table_already_exists:
                cursor.execute('''
                    CREATE TABLE book (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        author TEXT,
                        qty INTEGER
                        )
                    ''')
                self.conn.commit()
                print("Table called book create.")   

            books_to_insert = [
            (3001, "A Tale of Two Cities", "Charles Dickens", 30),
            (3002, "Harry Potter and the Philosopher's Stone", "J.K. Rowling", 40),
            (3003, "The Lion, the Witch and the Wardrobe", "C.S. Lewis", 25),
            (3004, "The Lord of the Rings", "J.R.R Tolkien", 37),
            (3005, "Alice in Wonderland", "Lewis Carroll", 12),
            (3006, "To Kill a Mockingbird", "Harper Lee", 55),
            (3007, "1984", "George Orwell", 33),
            (3008, "The Great Gatsby", "F. Scott Fitzgerald", 1),
            (3009, "War and Peace", "Leo Tolstoy", 23),
            (3010, "Beowolf", "J.R.R Tolkien", 6),
            (3011, "The Beautiful and Damned", "F. Scott Fitzgerald", 8),
            (3012, "A Tale of Two Cities", "Agatha Christie", 1056),
            ]

            # Convert titles and authors to uppercase for consistency in database
            books_to_insert = [(id, title.upper(), author.upper(), qty) for id, title, author, qty in books_to_insert]

            cursor.executemany("INSERT INTO book (id, title, author, qty) VALUES (?, ?, ?, ?)", books_to_insert)
            self.conn.commit()
            print("Pre-generated books added successfully.")

        except sqlite3.Error as e:
            print(f'Problem occured while trying to populate table with pre-generated books: {e}. Possibly already table exists.')
            self.rollback()

    def create_table(self):
        """
        Create a table referenced as 'book' in the database if one doesnt already exist.
        It stores info about the books inserted by the user, namely their title, author and amount of books (quantity). 
        It also gives an automated unique ID to the book when it needs to be called by a function.
        
        No arguements are taken
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    qty INTEGER
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f'Error creating the database table: {e}')
            raise

    def add_book(self, title, author, quantity=1):
        """
        Adds a book to the database by entering the title and author, a unique ID will be automatically assigned. 
        If a book with same title and author already exists, the user will be asked if he/she would want to add one 
        more to already existing quantity. If there is no existing book, then a new one is created and the user has an 
        option of updating the quantity of books.
        If no quantity is added, the new book is added to the database with a default quantity value of 1.
        
        Takes on arguements:
            title (string) which represents the title of the book.
            author (string) which represents the author of the book.
            quantity=1 (int) is the amount of books in the database. New books added has default setting of 1. 
        
        The title and author are converted to upper case in the database for consistency
        """
        try:
            # Convert to title case for books and authors to keep a consistent format in database
            title = title.upper()
            author = author.upper() 
            # Interact with the database by creating a cursor object
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, qty FROM book WHERE title = ? AND author = ?", (title, author))
            # Fetch the first row/next row of data from the database
            row = cursor.fetchone()
            if row:
                book_id, qty = row
                print(f'{qty} amount of "{title}" by "{author}" is already on the system...')
                add_more = input("Do you want to add 1 more to the quantity (yes/no)?:\n").strip().lower()
                
                if add_more == "yes":
                    cursor.execute("UPDATE book SET qty = ? WHERE id = ?", (qty +1, book_id))
                    print(f'One additional book added to the system for "{title}" by "{author}".')
                else:
                    print('Quantity remains unchanged.')
            else:
                # Give the user an option to update the quantity here for better user interface and efficiency
                print(f'New book "{title}" by "{author}" about to be added to the system...')
                add_quantity = input(f'Would you like to update the quantity for "{title}" by "{author}"? (yes/no)\n').strip().lower()
                if add_quantity == "yes":
                    updated_quantity = int(input(f'How many books of "{title}" by "{author}" would you like on the system?\n'))
                    cursor.execute("INSERT INTO book (title, author, qty) VALUES (?, ?, ?)", (title, author, updated_quantity))
                    print(f'{updated_quantity} books of "{title}" by "{author}" were added successfully.')
                else:
                    cursor.execute("INSERT INTO book (title, author, qty) VALUES (?, ?, ?)", (title, author, quantity))
                    print(f'New book "{title}" by "{author}" added successfully.')
                
                
            self.conn.commit()
        except sqlite3.Error as e:
            print(f'Error adding a book to the database: {e}')
            self.rollback() # Revert changes made if error found

    def update_book(self, title, author, quantity):
        """
        Update the quantity of a specific book with inserted title and author. Only need to update the quanitity as there is a menu option to delete a book.
        If the quantity is set to 0 then the book is removed from the database.
        If the book doesnt exist then notify the user and list all the books avaliable by the same author. The user can manually see if the book is on the system if its not correctly inputted. Give the option to update
        
        Arguements include the title (string), author (string) and quantity (int).
        """
        try:
            title = title.upper()
            author = author.upper()
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, qty FROM book WHERE title = ? AND author = ?", (title, author))
            row = cursor.fetchone()
            if row:
                book_id, old_qty = row
                print(f'{old_qty} book(s) of "{title}" by "{author}" is currently on the system.')
                
                if quantity == 0:
                    cursor.execute("DELETE FROM book WHERE id = ?", (book_id,))
                    print(f'"{title}" by "{author}" removed from the database')
                else:
                    cursor.execute("UPDATE book SET qty = ? WHERE id = ?", (quantity, book_id))
                    print(f'Quantity for "{title}" by "{author}" updated to {quantity}.')
            else:
                print(f'No book with the title "{title}" by "{author}" found in the database.')
            self.conn.commit()
        except sqlite3.Error as e:
            print("Problem occured while trying to update a book: {e}")
            self.rollback()

    def delete_book(self, title=None, author=None, book_id=None):
        """
        Delete a book from the database. If it doesnt exist then list all the books from the same author and ask the user if they which title they
        want to delete if any, else print that no books were deleted then return user to menu
        
        Takes on arguememts:
            title (string) and author (string) of the book
            book_id (int) is the books unique ID number that can be shown when searching for a book
        """
        try:
            cursor = self.conn.cursor()
            # Deleting by book's unique ID
            if book_id:
                cursor.execute("SELECT title, author FROM book WHERE id = ?", (book_id,))
                row = cursor.fetchone()
                if row:
                    title, author = row
                    confirm = input(f'Are you sure you want to delete book "{title}" by "{author}" from the system? (yes/no): ').strip().lower()
                    if confirm == "yes":
                        cursor.execute("DELETE FROM book WHERE id = ?", (book_id,))
                        print(f'Book "{title}" by "{author}" deleted from the system.')
                        self.conn.commit()
                    else:
                        print("Operation canceled... Returning to menu.")
                else:
                    print(f'No book with ID {book_id} found in the database.')
            
            else:
            # Deleting by books title AND author
                title = title.upper()
                author = author.upper()
                
                cursor.execute("SELECT id FROM book WHERE title = ? AND author = ?", (title, author))
                row = cursor.fetchone()
                if row:
                    book_id = row[0]
                    cursor.execute("DELETE FROM book WHERE id = ?", (book_id,))
                    print(f'"{title}" by "{author}" removed from the database.')
                else:
                    print(f'No book with the title "{title}" by "{author} found in the database.')
                self.conn.commit()
        except sqlite3.Error as e:
            print(f'Problem occured while trying to delete a book: {e}')
            self.rollback()

    def search_books(self, query, search_by_title=True, threshold=0.75):
        """
        Search books by title or author utilizing a matching search algorithm to find books with similar titles or authors, every search is converted to upper case
        since that is the format of the database. 
        Multiple instances of a book title may occur. List the books with the title searched and arrange them by author (alphabetically).
        If searched by author, list all the books by the author in alphabetical order.
        
        Handle mispelt/human error by adding a percentage error check for similar spelt titles or similar spelt books.
        
        Takes on arguements:
            query (string) which is the search query of title or author
            search_by_title (boolean statement). If its True, search by title. If not, search by author.
            threshold (float) 0-1 threshold to consider a similar matching title. 
            
        Searching by title:
        - First the code retrieves books from the database to find exact matches with the title
        - It calculates a 'matching score' for each book title
        - If there are no exact matches, similar titles are then recommended to the user (incase for spelling errors)
        - The code will sort it out with highest match first
        
        Searching by author:
        - All books are retrieved by matching author
        - If no match then the same check is done where suggestions are made that are above a match threshold (0.75 ~ 75%)
        - Books are printed out alphabetically       
        """
        try:
            query = query.upper()
            cursor = self.conn.cursor()
            
            if search_by_title:
                # Exact title match
                cursor.execute("SELECT id, title, author, qty FROM book")
                found_books = cursor.fetchall()
                
                found_books_with_threshold = []
                
                # Calculation for matching score for each book title with the search query
                for book in found_books:
                    title = book[1].upper()
                    # Using Levenshtein Distance to calculate a matching score
                    score = difflib.SequenceMatcher(None, query, title).ratio()
                    if score >= threshold:
                        found_books_with_threshold.append((book, score))
                
                if not found_books_with_threshold:
                    # Suggestion for corrected title if no match and threshold critera is met
                    corrected_title = self.suggested_corrected_title(query, [book[1] for book in found_books])
                    if corrected_title:
                        print(f'No books found. Did you mean: {corrected_title}?')
                    else: 
                        print("No books found.")
                    input("Press Enter to return to menu.\n")
                else:
                    # Results are displayed and sorted
                    # lambda function is the sorting key. List is sorted based on the index 1. Reverse = true is to sort  in descending order.
                    found_books_with_threshold = sorted(found_books_with_threshold, key=lambda x: x[1], reverse=True)
                    print("Similar search results:")
                    # Display the results in a readable format
                    print(f'{"ID":<8}{"Title":<55}{"Author":<30}{"Quantity":<8}')
                    for book, score in found_books_with_threshold:
                        print(f'{book[0]:<8}{book[1]:<55}{book[2]:<30}{book[3]:<8}')
                    
            else:
                # Author search
                cursor.execute("SELECT id, title, author, qty FROM book")
                found_books = cursor.fetchall()
                found_books_with_threshold = []
                
                for book in found_books:
                    # Calculation for matching score for each author with the search query using Levenshtein score
                    author = book[2].upper()
                    score = difflib.SequenceMatcher(None, query, author).ratio()
                    if score >= threshold:
                        found_books_with_threshold.append((book, score))
                
                if not found_books_with_threshold:
                    # Suggestion for corrected authors if no match and threshold critera is met
                    corrected_author = self.suggested_corrected_author(query, [book[2] for book in found_books])
                    if corrected_author:
                        print(f'No books found. Did you mean author: {corrected_author}?')
                    else:
                        print("No books found with that author.")
                        input("Press Enter to return to menu.\n")
                else:
                    # Results are displayed and sorted
                    found_books_with_threshold = sorted(found_books_with_threshold, key=lambda x: x[1], reverse=True)
                    print("Similar search results:")
                    print(f'{"ID":<8}{"Title":<55}{"Author":<30}{"Quantity":<8}')
                    for book, score in found_books_with_threshold:
                        print(f'{book[0]:<8}{book[1]:<55}{book[2]:<30}{book[3]:<8}')
        except sqlite3.Error as e:
            print(f'Problm occured searching for a book: {e}')
            raise
        
    def suggested_corrected_title(self, query, titles):
        """
        Find the best matching title in relation to the query for title.
        
        Arguements: 
        query (string) inputed by the user for a title and will be used to find a similar title
        titles (list) is a list of titles to be compared to with the query
        
        Returns None or a string with the best matches of the query
        """
        try:
            best_match = ""
            best_score = 0
            # Iterate through each title and calculate the score for a match
            for title in titles:
                score = difflib.SequenceMatcher(None, query, title).ratio()
                
                # Keep updating the best match if the score is higher
                if score > best_score:
                    best_match = title
                    best_score = score
            # Only return the match after the iteration if the score is greater than 0.75
            return best_match if best_score >= 0.75 else None
        except Exception as e:
            print(f'Error suggestion corrected title: {e}')
            raise
    
    def suggested_corrected_author(self, query, authors):
        """
        Find the closest match of authors with the query inputted by user with database.
        
        Arguements:
        query (string) inputed by the user for an author and will be used to find a similar author.
        authors (list) is a list of authors from database to be compared to with the query.
        
        Returns None or string with best matching author if above the threshold.
        """
        try:
            best_match = ""
            best_score = 0
            # Iterate through the authors then calculate matching score.
            for author in authors:
                score = difflib.SequenceMatcher(None, query, author).ratio()
                
                # Store the highest matching score of author
                if score > best_score:
                    best_match = author
                    best_score = score
                    
            # Only return if the match bets the threshold
            return best_match if best_score >= 0.75 else None
        except Exception as e:
            print(f'Problem occured while trying to suggest an author: {e}')
            raise
    
    def rollback(self):
        """
        Function to revert changes made when an error occurs. This maintains data consistency ensuring there isnt any invalid data added to the database
        """
        try:
            self.conn.rollback()
            print("Changes to database have been reverted.")
        except sqlite3.Error as e:
            print(f'Error trying to revert changes.')
            
    def close(self):
        """
        Close the database connection.
        """
        try:
            self.conn.close()
        except sqlite3.Error as e:
            print('Problem occured while trying to close the database: {e}')
            raise

def main():
    """
    Populate the table that was requested in the task. Only insert data if the table 'book' is emptry to prevent re-entries.

    Main function of the program to display a menu of choice for the user to select from:
        - Enter a new book with details of book id, title, author and amount of books
        - Update an existing book in the database
        - Delete a book from the database
        - Search for a book by either title, author or unique ID
        - End the program 
    """
    try:
        db = BookDatabase("ebookstore.db")

        # Populate the table on start up of the program
        db.populate_table()
        
        # Menu Options
        while True:
            print("\nMenu Options:")
            print("1. Enter book")
            print("2. Update book")
            print("3. Delete book")
            print("4. Search books")
            print("0. Exit")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                title = input("Enter the book title: ")
                author = input("Enter the author: ")
                db.add_book(title, author)
            elif choice == "2":
                title = input("Enter the book title to update: ")
                author = input("Enter the author of the book: ")
                quantity = int(input("Enter the new quantity (Enter 0 to delete the book): "))
                db.update_book(title, author, quantity)
            elif choice == "3":
                delete_option = input("Delete by Title/Author (T) or by books ID (I)?: ").strip().lower()
                if delete_option == "t":                  
                    title = input("Enter the book title to delete: ")
                    author = input("Enter the author of the book: ")
                    db.delete_book(title=title, author=author)
                elif delete_option == "i":
                    book_id = int(input("Enter the book's ID you want to delete: "))
                    db.delete_book(book_id=book_id)
                else:
                    print("Invalid Option. Input must be either 'T' or 'I'.")
            elif choice == "4":
                search_option = input("Search by Title (T) or Author (A): ").strip().lower()
                query = input("Enter the search query: ")
                if search_option == "t":
                    db.search_books(query, search_by_title=True)
                elif search_option == "a":
                    db.search_books(query, search_by_title=False)
                else:
                    print("Invalid search option. Please enter 'T' for title or 'A' for author.")
            elif choice == "0":
                db.close()
                break
            else:
                print("Invalid choice. Please enter a valid option.")
    except Exception as e:
        print(f'Unexpected error occured on the main program: {e}')
        
if __name__ == "__main__":
    main()
