from django.contrib import admin
from .models import *


admin.site.register(SGDocument, SGDocument.Admin)
admin.site.register(DBPediaEntity, DBPediaEntity.Admin)
