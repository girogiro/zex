from django.db import models
from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField


class Obdobie(models.Model):
	nazov = models.CharField(max_length=50, unique=True)
	zaciatok = models.DateField(blank=True, null=True)
	koniec = models.DateField(blank=True, null=True)

	class Meta:
		verbose_name_plural = 'Obdobia'
		ordering = ('zaciatok',)

	def __str__(self):
		return self.nazov


class Zasadnutie(models.Model):
	datum = models.DateField(unique=True)
	obdobie = models.ForeignKey(Obdobie)

	class Meta:
		verbose_name_plural = 'Zasadnutia'
		ordering = ('datum',)

	def __str__(self):
		return self.datum.strftime('%d.%m.%Y')


class Video(models.Model):
	nazov = models.CharField(max_length=100, unique=True)
	youtube_id = models.CharField(max_length=20, blank=True)
	zasadnutie = models.ForeignKey(Zasadnutie)

	class Meta:
		verbose_name_plural = 'Videá'
		ordering = ('zasadnutie__datum', 'nazov')
		
	def __str__(self):
		return self.nazov


class Bod(models.Model):
	cislo = models.DecimalField(max_digits=4, decimal_places=1)
	nazov = models.CharField(max_length=500, blank=True)
	predklada = models.CharField(max_length=200, blank=True)
	zasadnutie = models.ForeignKey(Zasadnutie)
	
	fts_text = models.TextField(blank=True)
	fts_index = VectorField()
	# namiesto default btree indexu sa pri `manage.py syncdb` vytvori GIN index vdaka custom SQL v zex/sql/bod.sql
	fts_index.db_index = False

	objects = SearchManager(
		fields = (('nazov', 'A'), ('predklada', 'B'), ('fts_text', 'B')),
		config = 'usimple',
		search_field = 'fts_index',
		auto_update_search_field = True
	)

	class Meta:
		verbose_name_plural = 'Body'
		unique_together = ('cislo', 'zasadnutie')
		ordering = ('zasadnutie__datum', 'cislo')

	def __str__(self):
		return '{0}. {1}'.format(self.cislo, self.nazov)


class Moment(models.Model):
	DRUHY = (
		('u', 'uvedenie bodu'),
		('v', 'vystúpenie rečníka'),
		('h', 'hlasovanie'),
		('i', 'iný'),
	)
	video = models.ForeignKey(Video)
	cas = models.IntegerField('čas (s)')
	druh = models.CharField(max_length=20, choices=DRUHY)
	nazov_prefix = models.CharField(max_length=100, blank=True)
	nazov_link = models.CharField(max_length=200)
	nazov_suffix = models.CharField(max_length=100, blank=True)
	anotacia = models.TextField(blank=True)
	bod = models.ForeignKey(Bod)

	class Meta:
		verbose_name_plural = 'Momenty'
		unique_together = ('video', 'cas')
		ordering = ('bod__zasadnutie__datum', 'bod__cislo', 'video__nazov', 'cas')

	def __str__(self):
		return '{0}:{1}: {2}'.format(self.video, self.cas, self.nazov_link)


###########################################################3
#
# class Osoba(models.Model):
	# meno = models.CharField(max_length=50)
	# priezvisko = models.CharField(max_length=50)
	# titul_pred = models.CharField(max_length=30, blank=True)
	# titul_za = models.CharField(max_length=20, blank=True)
	# email = models.EmailField(max_length=254, blank = True)

	# class Meta:
		# unique_together = ('meno', 'priezvisko')

	# def __str__(self):
		# return '{0} {1}'.format(self.meno, self.priezvisko)
