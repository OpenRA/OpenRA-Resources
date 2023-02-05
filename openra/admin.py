from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group

from openra.models import Engines, Maps
from openra.models import MapCategories
from openra.models import MapUpgradeLogs
from openra.models import Lints
from openra.models import Screenshots
from openra.models import Reports
from openra.models import Rating
from openra.models import Comments
from openra.models import UnsubscribeComments


class LatestRevisionListFilter(admin.SimpleListFilter):
    title = 'Latest Revision'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'latest_revision'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'yes':
            return queryset.filter(next_rev=0)
        if self.value() == 'no':
            return queryset.exclude(next_rev=0)


class MapsAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'

    def is_latest_revision(obj):
        return obj.next_rev == 0
    is_latest_revision.short_description = 'Latest Revision'
    is_latest_revision.boolean = True

    list_display = ('map_hash', 'title', 'user', 'posted', 'game_mod', 'amount_reports', 'mapformat', 'parser', 'advanced_map', 'lua', 'downloading', is_latest_revision)
    list_filter = ('game_mod', 'mapformat', 'advanced_map', 'lua', 'parser', LatestRevisionListFilter)


admin.site.register(Maps, MapsAdmin)

admin.site.register(MapCategories)


class MapUpgradeLogsAdmin(admin.ModelAdmin):
    ordering = ('-date_run',)
    list_display = ('map_id', 'date_run', 'from_version', 'to_version')
    list_filter = ('from_version', 'to_version')


admin.site.register(MapUpgradeLogs, MapUpgradeLogsAdmin)


class UnsubscribeCommentsAdmin(admin.ModelAdmin):
    date_hierarchy = 'unsubscribed'
    list_display = ('item_id', 'user', 'unsubscribed')


admin.site.register(UnsubscribeComments, UnsubscribeCommentsAdmin)


class CommentsAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'
    list_display = ('item_id', 'user', 'posted', 'content', 'item_type', 'is_removed')


admin.site.register(Comments, CommentsAdmin)


class LintsAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'
    list_display = ('map_id', 'version_tag', 'posted', 'pass_status')
    list_filter = ('pass_status',)


admin.site.register(Lints, LintsAdmin)


class ReportsAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'
    list_display = ('ex_id', 'user', 'posted', 'reason', 'infringement')
    list_filter = ('infringement',)


admin.site.register(Reports, ReportsAdmin)


class RatingAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'
    list_display = ('ex_id', 'user', 'posted', 'rating')


admin.site.register(Rating, RatingAdmin)


class ScreenshotsAdmin(admin.ModelAdmin):
    date_hierarchy = 'posted'
    list_display = ('ex_id', 'user', 'posted', 'map_preview')


admin.site.register(Screenshots, ScreenshotsAdmin)


class EnginesAdmin(admin.ModelAdmin):
    list_display = ('game_mod', 'version', 'is_playtest')


admin.site.register(Engines, EnginesAdmin)

# Add the registration date to the user list
UserAdmin.list_display = list(UserAdmin.list_display) + ['date_joined']
UserAdmin.ordering = ('-date_joined',)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Unregister unused models
admin.site.unregister(Group)
