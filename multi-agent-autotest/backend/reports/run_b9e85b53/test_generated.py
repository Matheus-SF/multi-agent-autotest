import pytest
from datetime import date, timedelta
from library import Book, Loan, Library

def test_book_post_init_valid():
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    assert book.isbn == "1234567890"
    assert book.title == "Test Book"
    assert book.author == "Author"
    assert book.copies == 1

def test_book_post_init_negative_copies():
    with pytest.raises(ValueError, match="Número de cópias não pode ser negativo"):
        Book(isbn="1234567890", title="Test Book", author="Author", copies=-1)

def test_book_post_init_empty_isbn():
    with pytest.raises(ValueError, match="ISBN não pode ser vazio"):
        Book(isbn="", title="Test Book", author="Author", copies=1)

def test_loan_is_overdue_not_returned():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() - timedelta(days=1))
    assert loan.is_overdue() is True

def test_loan_is_overdue_returned():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() - timedelta(days=1), returned=True)
    assert loan.is_overdue() is False

def test_loan_is_overdue_due_today():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today())
    assert loan.is_overdue() is False

def test_loan_days_overdue_not_overdue():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() + timedelta(days=1))
    assert loan.days_overdue() == 0

def test_loan_days_overdue_overdue():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() - timedelta(days=2))
    assert loan.days_overdue() == 2

def test_loan_fine_not_overdue():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() + timedelta(days=1))
    assert loan.fine() == 0.0

def test_loan_fine_overdue():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() - timedelta(days=2))
    assert loan.fine() == 1.0

def test_loan_fine_zero_rate():
    loan = Loan(book_isbn="1234567890", member_id="member1", loan_date=date.today(), due_date=date.today() - timedelta(days=2))
    assert loan.fine(rate_per_day=0.0) == 0.0

def test_library_init():
    library = Library()
    assert library._books == {}
    assert library._loans == []
    assert library._available == {}

def test_library_add_book_new():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    assert library._books["1234567890"] == book
    assert library._available["1234567890"] == 1

def test_library_add_book_existing():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    library.add_book(book)
    assert library._books["1234567890"].copies == 2
    assert library._available["1234567890"] == 2

def test_library_remove_book_not_found():
    library = Library()
    with pytest.raises(KeyError, match="Livro 1234567890 não encontrado"):
        library.remove_book("1234567890")

def test_library_remove_book_with_loans():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    library.borrow("1234567890", "member1", 7)
    with pytest.raises(ValueError, match="Não é possível remover: há cópias emprestadas"):
        library.remove_book("1234567890")

def test_library_borrow_book_not_found():
    library = Library()
    with pytest.raises(KeyError, match="Livro 1234567890 não encontrado"):
        library.borrow("1234567890", "member1", 7)

def test_library_borrow_no_copies_available():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    library.borrow("1234567890", "member1", 7)
    with pytest.raises(ValueError, match="Nenhuma cópia disponível de 1234567890"):
        library.borrow("1234567890", "member2", 7)

def test_library_borrow_invalid_days():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    with pytest.raises(ValueError, match="Prazo de empréstimo deve ser positivo"):
        library.borrow("1234567890", "member1", 0)

def test_library_return_book_not_found():
    library = Library()
    with pytest.raises(ValueError, match="Empréstimo ativo não encontrado para member1 / 1234567890"):
        library.return_book("1234567890", "member1")

def test_library_return_book_already_returned():
    library = Library()
    book = Book(isbn="1234567890", title="Test Book", author="Author", copies=1)
    library.add_book(book)
    loan = library.borrow("1234567890", "member1", 7)
    library.return_book("1234567890", "member1")
    with pytest.raises(ValueError, match="Empréstimo ativo não encontrado para member1 / 1234567890"):
        library.return_book("1234567890", "member1")

def test_library_available_copies_not_found():
    library = Library()
    with pytest.raises(KeyError, match="Livro 1234567890 não encontrado"):
        library.available_copies("1234567890")

def test_library_active_loans_none():
    library = Library()
    assert library.active_loans("member1") == []

def test_library_overdue_loans_none():
    library = Library()
    assert library.overdue_loans() == []

def test_library_search_by_author_not_found():
    library = Library()
    assert library.search_by_author("Unknown Author") == []

def test_library_search_by_author_partial_name():
    library = Library()
    book1 = Book(isbn="1234567890", title="Test Book", author="Author One", copies=1)
    book2 = Book(isbn="0987654321", title="Another Book", author="Author Two", copies=1)
    library.add_book(book1)
    library.add_book(book2)
    assert library.search_by_author("Author") == [book1, book2]
    assert library.search_by_author("One") == [book1]
    assert library.search_by_author("Two") == [book2]