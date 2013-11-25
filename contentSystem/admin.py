from django.contrib import admin

from contentSystem.models import Maps
from contentSystem.models import Units
from contentSystem.models import Palettes
from contentSystem.models import Reports
from contentSystem.models import Comments
from contentSystem.models import Screenshots

admin.site.register(Maps)
admin.site.register(Units)
admin.site.register(Palettes)
admin.site.register(Reports)
admin.site.register(Comments)
admin.site.register(Screenshots)
