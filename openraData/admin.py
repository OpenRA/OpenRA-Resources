from django.contrib import admin

from openraData.models import Maps
from openraData.models import Units
from openraData.models import Mods
from openraData.models import Palettes
from openraData.models import CrashReports
from openraData.models import Comments
from openraData.models import Screenshots

admin.site.register(Maps)
admin.site.register(Units)
admin.site.register(Mods)
admin.site.register(Palettes)
admin.site.register(CrashReports)
admin.site.register(Comments)
admin.site.register(Screenshots)
