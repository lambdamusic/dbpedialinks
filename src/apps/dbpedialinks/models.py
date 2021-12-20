from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.contrib import admin
from collections import Counter

import datetime

# See also: https://docs.djangoproject.com/en/1.10/topics/migrations/#workflow


class SGDocument(models.Model):
    """Model definition for SGDocument."""

    title = models.CharField(
        max_length=250,
        verbose_name="title",
        null=True,
        blank=True,
    )
    uri = models.URLField(max_length=300)

    author = models.CharField(
        blank=True, max_length=200, verbose_name="author")
    pubyear = models.IntegerField(
        blank=True, null=True, verbose_name="publication year", help_text="")
    description = models.TextField(
        blank=True,
        verbose_name="description (put everything in here for now)")

    dbentities = models.ManyToManyField('DBPediaEntity')

    class Meta:
        """Meta definition for SGDocument."""

        verbose_name = 'SGDocument'
        verbose_name_plural = 'SGDocuments'
        ordering = ["uri"]

    def __unicode__(self):
        """Unicode representation of SGDocument."""
        return self.uri

    class Admin(admin.ModelAdmin):
        list_display = ('id', 'title', 'uri')
        search_fields = ['id', 'title', 'uri']


class DBPediaEntity(models.Model):
    """Model definition for DBPediaEntity."""

    title = models.CharField(
        max_length=250,
        verbose_name="title",
        null=True,
        blank=True,
    )
    uri = models.URLField(max_length=300)

    totarticles = models.IntegerField(
        null=True, blank=True, verbose_name="Tot associated articles")
    dbtype = models.CharField(
        blank=True, max_length=200, verbose_name="dbtype")
    description = models.TextField(
        blank=True,
        verbose_name="description (put everything in here for now)")
    top_rel_subjects = models.ManyToManyField(
        'self',
        through='Subject_Rel',
        symmetrical=False,
        # related_name="subject2",
        through_fields=('subject1', 'subject2'),
    )

    class Meta:
        """Meta definition for DBPediaEntity."""

        verbose_name = 'DBPedia Entity'
        verbose_name_plural = 'DBPedia Entities'
        ordering = ["title"]

    def __unicode__(self):
        """Unicode representation of DBPediaEntity."""
        return self.uri

    def update_tot_count(self):
        self.totarticles = self.sgdocument_set.count()
        self.save()

    # PS once calculated, used the <top_rel_subjects> method instead!
    def related_subjects(self, size=99999999, articles_set=None, CACHE=False):
        """
        Compute co-occurring subjects across whole publications; returns a list of tuples [(subj, count)] sorted by max count descencing

        NOTE this can be cached in the DB using the CACHE flag!  

        <articles_set> : allows to pass manually a queryset for extracting co-occurrence data
        """

        def count_and_reduce(lista, size):
            "reduce by taking first N elements sorted by tot count"
            c = Counter(lista)
            out = c.items()
            out = sorted(out, key=lambda t: (t[1], t[0].title), reverse=True)
            print(
                "Found:",
                len(out),
                "Keep:",
                size,
            )
            return out[:size]

        if not articles_set:
            articles_set = self.sgdocument_set.all()
        # approach 1: use co-occurrnce to define relatedness
        related = []
        for a in articles_set:
            related += a.dbentities.exclude(id=self.id)
        out = count_and_reduce(related, size)

        if CACHE:
            for this in out:
                print("Caching %s ... " % str(this))
                rel = Subject_Rel.objects.create(
                    subject1=self, subject2=this[0], score=this[1])

        # finally return a dict
        return out

    class Admin(admin.ModelAdmin):
        list_display = ('id', 'title', 'uri')
        search_fields = ['id', 'title', 'uri']


class Subject_Rel(models.Model):
    subject1 = models.ForeignKey(
        DBPediaEntity,
        on_delete=models.CASCADE,
        related_name="is_subject_in_relations")
    subject2 = models.ForeignKey(
        DBPediaEntity,
        on_delete=models.CASCADE,
        related_name="is_object_in_relations")
    score = models.IntegerField(null=True)