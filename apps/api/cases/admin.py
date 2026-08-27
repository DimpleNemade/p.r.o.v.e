from django.contrib import admin
from .models import Case, CaseParticipant

admin.site.register([Case, CaseParticipant])
