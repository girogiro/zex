from collections import OrderedDict
from datetime import datetime
import re

from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string

from zex.models import *


def index(request, datum_zasadnutia, cislo_bodu):
	hladany_text = request.GET.get('q')
		
	if not datum_zasadnutia and not cislo_bodu and not hladany_text:
		context = {'oznam': 'Treba zadať aspoň jedno kritérium vyhľadávania.'}
		return render(request, 'zex/index.html', context)
	
	# najdenie vsetkych bodov vyhovujucich zadanym kriteriam
	body = Bod.objects.all()
	if hladany_text:
		# slova sa beru ako prefixy a medzi nich sa prida AND
		hladany_text = re.sub(r'\W', ' ', hladany_text).strip()
		hladany_text = re.sub(r'\b ', ':* & ', hladany_text)
		hladany_text += ':*'
		body = Bod.objects.search(hladany_text, raw=True)

	if datum_zasadnutia:
		d = datetime.strptime(datum_zasadnutia, '%d.%m.%Y')
		body = body.filter(zasadnutie__datum=d)
		
	if cislo_bodu:
		body = body.filter(cislo=cislo_bodu)

	# najdenie vsetkych momentov v najdenych bodoch
	momenty = Moment.objects.filter(bod__in=body)
	momenty = momenty.select_related('bod', 'bod__zasadnutie', 'video')
	
	# rozdelenie vsetkych momentov k najdenym bodom do hierarchie zasadnutie-bod-moment
	zasadnutia = OrderedDict()
	for moment in momenty:
		zid = moment.bod.zasadnutie_id
		if zid not in zasadnutia:
			zasadnutia[zid] = { 'polia': moment.bod.zasadnutie, 'body': OrderedDict() }
		bid = moment.bod_id
		if bid not in zasadnutia[zid]['body']:
			zasadnutia[zid]['body'][bid] = { 'polia': moment.bod, 'momenty': [] }
		zasadnutia[zid]['body'][bid]['momenty'].append(moment)
	zasadnutia = zasadnutia.values()
	for zasadnutie in zasadnutia:
		zasadnutie['body'] = zasadnutie['body'].values()
		
	prvy_moment = momenty.first() if momenty else ''
	
	context = {
		'najdene_zasadnutia': zasadnutia,
		'prvy_moment': prvy_moment,
		'oznam': 'Nič sa nenašlo.'
	}
	
	# from django.db import connection
	# print(len(connection.queries))
	# with open('queries', 'w', encoding = 'utf-8', newline = '\n') as f:
		# print(connection.queries, file=f)
	
	return render(request, 'zex/index.html', context)


from zex.update import update_data
def update(request):
	z, v, b, m = update_data()
	_uloz_body_zasadnuti()
	context = { 'zasadnuti': z, 'videi': v, 'bodov': b, 'momentov': m }
	return render(request, 'zex/update.html', context)

def _uloz_body_zasadnuti():
	body = Bod.objects.select_related('zasadnutie')
	
	# rozdelenie vsetkych bodov do hierarchie zasadnutie-bod
	zasadnutia = OrderedDict()
	for bod in body:
		zid = bod.zasadnutie_id
		if zid not in zasadnutia:
			zasadnutia[zid] = { 'polia': bod.zasadnutie, 'body': [] }
		zasadnutia[zid]['body'].append(bod)
	zasadnutia = zasadnutia.values()
	
	context = { 'zasadnutia': zasadnutia }
	js = render_to_string('zex/zasadnutia.js', context)
	
	with open('/var/www/zex/zex/static/zex/js/zasadnutia.js', 'w', encoding='utf-8', newline='') as file:
		file.write(js)
