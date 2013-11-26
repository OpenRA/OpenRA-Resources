from django.contrib import admin

from openraData.models import Maps
from openraData.models import Units
from openraData.models import Palettes
from openraData.models import Reports
from openraData.models import Comments
from openraData.models import Screenshots

admin.site.register(Maps)
admin.site.register(Units)
admin.site.register(Palettes)
admin.site.register(Reports)
admin.site.register(Comments)
admin.site.register(Screenshots)
