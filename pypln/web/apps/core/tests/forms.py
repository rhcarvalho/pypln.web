# coding: utf-8
#
# Copyright 2012 NAMD-EMAP-FGV
#
# This file is part of PyPLN. You can get more information at: http://pypln.org/.
#
# PyPLN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyPLN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyPLN.  If not, see <http://www.gnu.org/licenses/>.

from StringIO import StringIO

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from core.models import Document
from core.forms import DocumentForm

__all__ = ["DocumentFormTest"]

class DocumentFormTest(TestCase):
    fixtures = ['corpus']

    def setUp(self):
        self.url = reverse('corpus_page',
            kwargs={'corpus_slug': 'test-corpus'})
        self.user = User.objects.all()[0]

        self.fp = StringIO("Bring us a shrubbery!!")
        self.fp.name = "42.txt"

        self.fp2 = StringIO("Bring us another shrubbery!!")
        self.fp2.name = "43.txt"

        self.request_factory = RequestFactory()

    def tearDown(self):
        self.fp.close()
        self.fp2.close()

    def test_form_is_valid_with_one_file(self):
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertTrue(form.is_valid())

    def test_at_least_one_file_is_required(self):
        request = self.request_factory.post(self.url, {"blob": []})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertFalse(form.is_valid())

    def test_form_is_valid_with_multiple_files(self):
        request = self.request_factory.post(self.url,
                                            {"blob": [self.fp, self.fp2]})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertTrue(form.is_valid())

    def test_form_saves_document_with_correct_user(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save()
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 1)

    def test_form_saves_document_with_correct_content(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save()
        self.assertEqual(len(Document.objects.all()), 1)
        doc = Document.objects.all()[0]
        self.assertEqual(doc.blob.read(), "Bring us a shrubbery!!")

    def test_save_raises_ValueError_if_data_isnt_valid(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": []})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertRaises(ValueError, form.save)

    def test_form_only_returns_document_if_commit_is_false(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        docs = form.save(commit=False)
        self.assertEqual(docs[0].owner, self.user)
        self.assertEqual(len(Document.objects.all()), 0)

    def test_blob_widget_has_multiple_attr(self):
        request = self.request_factory.post(self.url, {"blob": self.fp})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertEqual(form.fields['blob'].widget.attrs['multiple'],
                         'multiple')

    def test_form_saves_more_than_one_document(self):
        self.assertEqual(len(Document.objects.all()), 0)
        request = self.request_factory.post(self.url, {"blob": [self.fp, self.fp2]})
        form = DocumentForm(self.user, request.POST, request.FILES)
        form.is_valid()
        form.save()
        self.assertEqual(len(Document.objects.all()), 2)
        doc1, doc2 = Document.objects.all()
        self.assertEqual(doc1.blob.read(), "Bring us a shrubbery!!")
        self.assertEqual(doc2.blob.read(), "Bring us another shrubbery!!")

    def test_form_is_not_valid_with_filename_longer_than_100_chars(self):
        file_with_long_name = StringIO("This file will have a really long name.")
        file_with_long_name.name = "f" * 100

        request = self.request_factory.post(self.url,
                                            {"blob": file_with_long_name})
        form = DocumentForm(self.user, request.POST, request.FILES)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.has_key('blob'))
