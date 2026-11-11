from datetime import timedelta
from secrets import token_urlsafe

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from library.models import Author, Book, BookCopy, EventLog, Loan, Reader, Reservation


class ModelTests(SimpleTestCase):
    def test_loan_overdue_only_when_unreturned_and_past_due(self):
        today = timezone.localdate()
        loan = Loan(due_at=today)
        self.assertFalse(loan.is_overdue)
        loan.due_at = today - timedelta(days=1)
        self.assertTrue(loan.is_overdue)
        loan.returned_at = today
        self.assertFalse(loan.is_overdue)

    def test_unavailable_copy_fails_model_validation(self):
        copy = BookCopy(pk=1, status=BookCopy.Status.REPAIR)
        with self.assertRaises(ValidationError):
            Loan(copy=copy).clean()


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first = Book.objects.create(title="Atlas", isbn="9781234567897")
        cls.second = Book.objects.create(title="Botany")
        author = Author.objects.create(name="Anna Field")
        cls.first.authors.add(author)
        BookCopy.objects.create(book=cls.first, inventory_number="CAT-01")
        BookCopy.objects.create(
            book=cls.first, inventory_number="CAT-02", status=BookCopy.Status.LOANED
        )
        BookCopy.objects.create(
            book=cls.second, inventory_number="CAT-03", status=BookCopy.Status.RESERVED
        )

    def test_catalog_is_public_and_shows_books(self):
        response = self.client.get(reverse("library:catalog"))
        self.assertContains(response, self.first.title)
        self.assertContains(response, self.second.title)

    def test_catalog_searches_title_author_and_isbn(self):
        for query in ("atlas", "field", "4567897"):
            with self.subTest(query=query):
                response = self.client.get(reverse("library:catalog"), {"q": query})
                self.assertEqual(list(response.context["books"]), [self.first])

    def test_authors_and_book_detail_render_availability(self):
        response = self.client.get(reverse("library:authors"))
        self.assertContains(response, "Anna Field")
        for book, status, count in (
            (self.first, "available", 1),
            (self.second, "reserved", 0),
        ):
            with self.subTest(book=book.title):
                response = self.client.get(reverse("library:book_detail", args=[book.pk]))
                self.assertContains(response, book.title)
                self.assertEqual(response.context["book"].catalog_status, status)
                self.assertEqual(response.context["book"].available_count, count)


class AccountTests(TestCase):
    def test_signup_creates_reader_and_starts_session(self):
        password = token_urlsafe(20)
        response = self.client.post(reverse("library:signup"), {
            "username": "new-reader", "full_name": "New Reader",
            "email": "reader@example.test", "password1": password, "password2": password,
        })
        self.assertRedirects(response, reverse("library:catalog"))
        reader = Reader.objects.get(user__username="new-reader")
        self.assertEqual(reader.full_name, "New Reader")
        self.assertEqual(reader.ticket_number, f"R-{reader.user_id:04d}")
        self.assertEqual(self.client.session["_auth_user_id"], str(reader.user_id))

    def test_login_requires_correct_password(self):
        password = token_urlsafe(20)
        user = User.objects.create_user("reader", password=password)
        response = self.client.post(reverse("login"), {"username": user.username, "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("login"), {"username": user.username, "password": password})
        self.assertRedirects(response, reverse("library:catalog"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_staff_and_admin_routes_check_role(self):
        reader = User.objects.create_user("ordinary")
        admin = User.objects.create_user("staff", is_staff=True, is_superuser=True)
        for route in ("library:readers", "admin:index"):
            with self.subTest(route=route):
                url = reverse(route)
                self.client.force_login(reader)
                self.assertEqual(self.client.get(url).status_code, 302)
                self.client.force_login(admin)
                self.assertEqual(self.client.get(url).status_code, 200)


class CirculationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user("librarian", is_staff=True)
        cls.user = User.objects.create_user("reader")
        cls.reader = Reader.objects.create(user=cls.user, full_name="Reader", ticket_number="R-1")
        cls.other = Reader.objects.create(full_name="Other Reader", ticket_number="R-2")
        cls.book = Book.objects.create(title="Circulation")
        cls.copy = BookCopy.objects.create(book=cls.book, inventory_number="CIRC-1")
        cls.other_copy = BookCopy.objects.create(book=cls.book, inventory_number="CIRC-2")

    def setUp(self):
        self.client.force_login(self.staff)

    def loan_data(self):
        return {
            "copy": self.copy.pk, "reader": self.reader.pk,
            "due_at": timezone.localdate() + timedelta(days=7),
        }

    def test_issue_and_return_update_copy_and_log_once(self):
        response = self.client.post(reverse("library:loan_create"), self.loan_data())
        self.assertRedirects(response, reverse("library:loans"))
        loan = Loan.objects.get(copy=self.copy)
        self.assertEqual(loan.reader, self.reader)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.LOANED)
        self.assertTrue(EventLog.objects.filter(action="Оформлена выдача", user=self.staff).exists())

        url = reverse("library:loan_return", args=[loan.pk])
        for _ in range(2):
            self.assertRedirects(self.client.post(url), reverse("library:loans"))
        self.copy.refresh_from_db()
        loan.refresh_from_db()
        self.assertEqual(self.copy.status, BookCopy.Status.AVAILABLE)
        self.assertEqual(loan.returned_at, timezone.localdate())
        self.assertEqual(EventLog.objects.filter(action="Оформлен возврат").count(), 1)

    def test_second_issue_is_rejected(self):
        data = self.loan_data()
        self.client.post(reverse("library:loan_create"), data)
        data["reader"] = self.other.pk
        response = self.client.post(reverse("library:loan_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].has_error("copy", "invalid_choice"))
        self.assertEqual(Loan.objects.filter(copy=self.copy).count(), 1)

    def test_create_and_search_readers(self):
        response = self.client.post(reverse("library:reader_create"), {
            "full_name": "Third Reader", "ticket_number": "R-3", "active": "on",
        })
        self.assertRedirects(response, reverse("library:readers"))
        created = Reader.objects.get(ticket_number="R-3")
        response = self.client.get(reverse("library:readers"), {"q": "R-3"})
        self.assertEqual(list(response.context["readers"]), [created])

    def test_reservation_can_be_created_and_fulfilled(self):
        response = self.client.post(reverse("library:reservation_create"), {
            "reader": self.reader.pk, "book": self.book.pk,
        })
        self.assertRedirects(response, reverse("library:reservations"))
        reservation = Reservation.objects.get(reader=self.reader, book=self.book)
        self.assertEqual(reservation.status, Reservation.Status.ACTIVE)
        response = self.client.post(reverse("library:reservation_action", args=[reservation.pk, "fulfill"]))
        self.assertRedirects(response, reverse("library:reservations"))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.FULFILLED)

    def test_overdue_report_excludes_returned_loan(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        due = Loan.objects.create(copy=self.copy, reader=self.reader, due_at=yesterday)
        Loan.objects.create(copy=self.other_copy, reader=self.other, due_at=yesterday, returned_at=yesterday)
        response = self.client.get(reverse("library:overdue_report"))
        self.assertEqual(list(response.context["loans"]), [due])

    def test_cabinet_is_scoped_to_signed_in_reader(self):
        own_loan = Loan.objects.create(copy=self.copy, reader=self.reader, due_at=timezone.localdate())
        Loan.objects.create(copy=self.other_copy, reader=self.other, due_at=timezone.localdate())
        own_reservation = Reservation.objects.create(book=self.book, reader=self.reader)
        Reservation.objects.create(book=self.book, reader=self.other)
        self.client.force_login(self.user)
        response = self.client.get(reverse("library:cabinet"))
        self.assertEqual(response.context["reader"], self.reader)
        self.assertEqual(list(response.context["loans"]), [own_loan])
        self.assertEqual(list(response.context["reservations"]), [own_reservation])
