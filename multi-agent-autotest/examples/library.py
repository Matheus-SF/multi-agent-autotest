from datetime import date, timedelta
from dataclasses import dataclass, field


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    copies: int = 1

    def __post_init__(self):
        if self.copies < 0:
            raise ValueError("Número de cópias não pode ser negativo")
        if not self.isbn:
            raise ValueError("ISBN não pode ser vazio")


@dataclass
class Loan:
    book_isbn: str
    member_id: str
    loan_date: date
    due_date: date
    returned: bool = False
    return_date: date | None = None

    def is_overdue(self) -> bool:
        if self.returned:
            return False
        return date.today() > self.due_date

    def days_overdue(self) -> int:
        if not self.is_overdue():
            return 0
        return (date.today() - self.due_date).days

    def fine(self, rate_per_day: float = 0.50) -> float:
        return self.days_overdue() * rate_per_day


class Library:
    def __init__(self):
        self._books: dict[str, Book] = {}
        self._loans: list[Loan] = []
        self._available: dict[str, int] = {}

    def add_book(self, book: Book) -> None:
        if book.isbn in self._books:
            self._books[book.isbn].copies += book.copies
            self._available[book.isbn] += book.copies
        else:
            self._books[book.isbn] = book
            self._available[book.isbn] = book.copies

    def remove_book(self, isbn: str) -> None:
        if isbn not in self._books:
            raise KeyError(f"Livro {isbn} não encontrado")
        if self._available[isbn] < self._books[isbn].copies:
            raise ValueError("Não é possível remover: há cópias emprestadas")
        del self._books[isbn]
        del self._available[isbn]

    def borrow(self, isbn: str, member_id: str, days: int = 14) -> Loan:
        if isbn not in self._books:
            raise KeyError(f"Livro {isbn} não encontrado")
        if self._available[isbn] == 0:
            raise ValueError(f"Nenhuma cópia disponível de {isbn}")
        if days <= 0:
            raise ValueError("Prazo de empréstimo deve ser positivo")

        loan = Loan(
            book_isbn=isbn,
            member_id=member_id,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=days)
        )
        self._available[isbn] -= 1
        self._loans.append(loan)
        return loan

    def return_book(self, isbn: str, member_id: str) -> Loan:
        for loan in reversed(self._loans):
            if loan.book_isbn == isbn and loan.member_id == member_id and not loan.returned:
                loan.returned = True
                loan.return_date = date.today()
                self._available[isbn] += 1
                return loan
        raise ValueError(f"Empréstimo ativo não encontrado para {member_id} / {isbn}")

    def available_copies(self, isbn: str) -> int:
        if isbn not in self._available:
            raise KeyError(f"Livro {isbn} não encontrado")
        return self._available[isbn]

    def active_loans(self, member_id: str) -> list[Loan]:
        return [l for l in self._loans if l.member_id == member_id and not l.returned]

    def overdue_loans(self) -> list[Loan]:
        return [l for l in self._loans if l.is_overdue()]

    def search_by_author(self, author: str) -> list[Book]:
        return [b for b in self._books.values() if author.lower() in b.author.lower()]
