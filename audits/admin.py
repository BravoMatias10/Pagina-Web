from django.contrib import admin
from .models import Audit, Review, Event
admin.site.register([Audit,Review,Event])
admin.site.site_header='Audita · Administración'
