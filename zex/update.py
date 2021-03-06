#!/usr/bin/python3	
# -*- coding: utf-8 -*-

import sys
import csv
import re
from datetime import datetime
import io
import requests
import json

from zex.models import *

# link na Google spreadsheet s datami
DATA_SPREADSHEET = 'https://spreadsheets.google.com/feeds/worksheets/1XZwKlfZBuIZC_H97_a5SYnc-XogERwsafYj8RMWbtqA/public/basic?alt=json'

# regex nahradenia pre vycistenie a upravu prepisov zasadnuti
NAHRADENIA = [
	# nahradenie whitespace medzerami
	(r'\s', ' ', 0),
	# nahradenie aspon 3 medzier za sebou novym riadkom
	(r' {3,}', '\n', 0),
	# nahradenie viacerych medzier za sebou jednou medzerou
	(r' {2,}', ' ', 0),
	# zmazanie medzier na koncoch riadku
	(r'\s+$', '', re.MULTILINE),
	# zmazanie datumov na zaciatku
	(r'^\d{1,2}.\d{1,2}.\d{4}\s', '', 0),
	# pridanie medzery za cislom s bodkou
	(r'(\d\w*)\.\b', r'\1. ', 0),
	# pridanie medzery v pripade "c."
	(r'č\.\b', r'č. ', 0),
	# nahradenie "Hlasovanie o bode <n>. <nazov>" na "Hlasovanie o uzneseni"
	(r'Hlasovanie (o bode|k bodu) \d\w*\..*', 'Hlasovanie o uznesení', re.MULTILINE),
	# zmazanie "k bodu <n>. <nazov>"
	(r' k bodu \d\w*\..*', '', re.MULTILINE),
	# pripojenie "Ohladne" k predchadzajucej vete
	(r'\s+-?[Oo]hľadne', ' ohľadne', 0),
	# zrusenie titulov
	(r'(Bc.|Mgr.|Ing.|JUDr.|MUDr.|MVDr.|ThDr.|RNDr.|RSDr.|PhDr.|PaedDr.|art.|arch.|Dipl.|doc.|prof.|, ?PhD.|, ?DrSc.) ?', '', 0),
	# doplnenie medzery sa znak odrazky
	(r'^-\b', r'- ', re.MULTILINE),
]

# zoznam volebnych obdobi ako trojic (nazov, zaciatok, koniec)
obdobia = []
# mapovanie z nazvu suboru s videom na jeho YouTube ID
video_ytid = {}

def stiahni_csv(url):
	'''Stiahne CSV súbor z danej URL a a vráti ho.
	'''
	resp = requests.get(url)
	resp.raise_for_status()
	file = io.StringIO(resp.content.decode('utf-8'), newline='')
	return [riadok for riadok in csv.reader(file)]


def cas_na_sekundy(casstr):
	'''Vráti pre čas v tvare 0:12:34 počet sekúnd, ktoré reprezentuje (tu 754).
	'''
	dt = datetime.strptime(casstr, '%H:%M:%S')
	return dt.hour * 3600 + dt.minute * 60 + dt.second


def formatuj(text):
	'''Do textu pridá HTML značky (pre odstavce a zoznamy odrážok) a vráti upravený text.'''
	# pridanie znaciek <p> na vsetky riadky okrem odrazok
	text = re.sub(r'^([^-].*)', r'<p>\1</p>', text, flags=re.MULTILINE)
	# prevod zoznamov odrazok do HTML
	text = re.sub(r'^- ?(.*)', r'\t<li>\1</li>', text, flags=re.MULTILINE)
	text = re.sub(r'(?<!</li>\n)(\t<li>.*?</li>)', r'<ul>\n\1', text, flags=re.DOTALL)
	text = re.sub(r'(\t<li>.*?</li>)(?!\n\t<li>)', r'\1\n</ul>', text, flags=re.DOTALL)
	return text


def update_data():
	'''Aktualizuje dáta zo zdrojového spreadsheetu.
	'''
	# zozbieraj linky na jednotlive listy spreadsheetu
	resp = requests.get(DATA_SPREADSHEET)
	resp.raise_for_status()
	spreadsheet = resp.json()
	sheet_urls = []
	for sheet in spreadsheet['feed']['entry']:
		sheet_urls.extend([link['href'] for link in sheet['link'] if link['type'] == 'text/csv'])

	# z prveho listu vytvor zoznam volebnych obdobi
	url = sheet_urls.pop(0)
	obdobia_csv = stiahni_csv(url)
	obdobia_csv.pop(0)
	global obdobia
	for riadok in obdobia_csv:
		nazov = riadok[0].strip()
		zac = datetime.strptime(riadok[1].replace(' ', ''), '%d.%m.%Y').date()
		kon = datetime.strptime(riadok[2].replace(' ', ''), '%d.%m.%Y').date() if riadok[2] else None
		obdobia.append((nazov, zac, kon))

	# z druheho listu vytvor mapovanie z nazvu videa na jeho YouTube ID
	url = sheet_urls.pop(0)
	videa_csv = stiahni_csv(url)
	videa_csv.pop(0)
	global video_ytid
	for riadok in videa_csv:
		ytid = re.search(r'\?v=(\w+)', riadok[1])
		video_ytid[riadok[0].strip()] = ytid.group(1) if ytid else ''

	# updatuj data z jednotlivych listov
	for url in sheet_urls:
		update_from_sheet(url)
	
	# vrat pocet objektov v databaze
	return (
		Obdobie.objects.count(),
		Zasadnutie.objects.count(),
		Video.objects.count(),
		Bod.objects.count(),
		Moment.objects.count()
	)


def update_from_sheet(url):
	'''Aktualizuje dáta z jedného listu zdrojového spreadsheetu.
	'''
	# nacitaj momenty zasadnuti
	momenty_csv = stiahni_csv(url)
	momenty_csv.pop(0)

	# precisti texty v anotaciach momentov
	for n in NAHRADENIA:
		p = re.compile(n[0], flags = n[2])
		for riadok in momenty_csv:
			riadok[3] = p.sub(n[1], riadok[3])

	# zapis precistene texty pre kontrolu
#	with open('precistene_data.csv', 'w', encoding = 'utf-8', newline = '') as f:
#		csv.writer(f).writerows(momenty_csv)

	obdobia_v_db = { o.nazov: o for o in Obdobie.objects.all() }
	videa_v_db = { v.nazov: v for v in Video.objects.all() }
	zasadnutia_v_db = { z.datum: z for z in Zasadnutie.objects.all() }

	# aktualizuj momenty v databaze
	for riadok in momenty_csv:
		datum = datetime.strptime(riadok[0].replace(' ', ''), '%d.%m.%Y').date()
		video_nazov = riadok[1]
		cas = cas_na_sekundy(riadok[2])
		text = riadok[3]

		# najdi zasadnutie pre datum na riadku, pripadne vloz nove
		try:
			z = zasadnutia_v_db[datum]
		except KeyError:
			# najdi volebne obdobie zasadnutia, pripadne vloz nove
			obdobie = [o for o in obdobia if (not o[1] or datum>=o[1]) and (not o[2] or datum<=o[2])]
			if not obdobie:
				raise RuntimeError('V zozname volebných období chýba obdobie pre zasadnutie %s' % datum)
			obdobie = obdobie[0]
			try:
				o = obdobia_v_db[obdobie[0]]
			except KeyError:
				o = Obdobie(nazov=obdobie[0], zaciatok=obdobie[1], koniec=obdobie[2])
				o.save()
				obdobia_v_db[obdobie[0]] = o
			z = Zasadnutie(datum=datum, obdobie=o)
			z.save()
			zasadnutia_v_db[datum] = z

		# najdi video pre nazov videa na riadku, pripadne vloz nove
		try:
			v = videa_v_db[video_nazov]
		except KeyError:
			ytid = video_ytid[video_nazov] if video_nazov in video_ytid.keys() else ''
			v = Video(nazov=video_nazov, youtube_id=ytid, zasadnutie=z)
			v.save()
			videa_v_db[video_nazov] = v

		try:
			m = Moment.objects.get(video=v, cas=cas)
		except Moment.DoesNotExist:
			m = Moment(video=v, cas=cas)

		# je na riadku uvedenie bodu?
		if '\n' in text:
			t = re.match(r'(\d\w*)\. (.*?)\n(.*)$', text, flags=re.DOTALL)
		else:
			t = re.match(r'(\d\w*)\. (.*)$()', text)
		if t:
			m.druh = 'u'
			m.nazov_link = 'Uvedenie bodu'
			m.nazov_prefix = m.nazov_suffix = m.anotacia = ''

			# najdi prislusny bod, pripadne vloz novy bod
			cislo = t.group(1) or ''
			try:
				b = Bod.objects.get(cislo=cislo, zasadnutie=z)
			except Bod.DoesNotExist:
				b = Bod(cislo=cislo, zasadnutie=z)
			b.nazov = t.group(2) or ''
			b.predklada = t.group(3) or ''
			b.fts_text = b.nazov + ' ' + b.predklada
			b.save()

		else:
			# je na riadku hlasovanie?
			if '\n' in text:
				t = re.match(r'(Hlasovanie.*?)\n(.*)$', text, flags=re.DOTALL)
			else:
				t = re.match(r'(Hlasovanie.*)$()', text)
			if t:
				m.druh = 'h'
				m.nazov_link = t.group(1) or ''
				m.anotacia = formatuj(t.group(2)) or ''
				m.nazov_prefix = m.nazov_suffix = ''

			else:
				# je na riadku vystupenie recnika?
				t = re.match(r'(.+?)\b([A-ZÁÄČĎÉĚÍĹĽŇÓÔRŔŘŠŤÚŮÝŽ].*?)?(,.*?)?\n(.*)$', text, flags=re.DOTALL)
				if t:
					m.druh = 'v'
					m.nazov_prefix = t.group(1) or ''
					m.nazov_link = t.group(2) or ''
					m.nazov_suffix = t.group(3) or ''
					m.anotacia = formatuj(t.group(4)) or ''
					if not m.nazov_link:
						m.nazov_link = m.nazov_prefix
						m.nazov_prefix = ''

				else:
					# iný moment
					m.druh = 'i'
					m.nazov_link = text
					m.nazov_prefix = m.nazov_suffix = m.anotacia = ''

		m.bod = b
		m.save()

		# pridaj texty momentu do suhrnu v bode pouzivaneho na fulltextove vyhladavanie
		b.fts_text += ' ' + ' '.join((m.nazov_prefix, m.nazov_link, m.nazov_suffix, m.anotacia))
		b.save()


# DEVEL
import unicodedata
def bez_diakritiky(text):
	if text: return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()

# from django.db import connection
# print(len(connection.queries))
# with open('queries', 'w', encoding = 'utf-8', newline = '') as f:
	# print(connection.queries, file=f)

# print(Zasadnutie.objects.count())
# print(Video.objects.count())
# print(Bod.objects.count())
# print(Moment.objects.count())
