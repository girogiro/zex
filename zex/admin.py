from django.contrib import admin
from zex.models import Zasadnutie, Video, Bod, Moment

class MomentAdmin(admin.ModelAdmin):
	fieldsets = [
		(None, {'fields': ['video', 'cas']}),
		('Čo sa udialo', {'fields': ['druh', 'nazov_prefix', 'nazov_link', 'nazov_suffix', 'anotacia']}),
		('Kam patrí', {'fields': ['bod']}),
	]
	list_display = ['video', 'cas', 'nazov_link', 'bod']
	list_filter = ['video', 'bod']
	search_fields = ['nazov_link']

admin.site.register(Zasadnutie)
admin.site.register(Video)
admin.site.register(Bod)
admin.site.register(Moment, MomentAdmin)