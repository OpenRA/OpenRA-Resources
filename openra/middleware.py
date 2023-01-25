from django.conf import settings
from django.http import HttpResponse
from django.template import loader


class ShowMaintenanceModeViewIfEnabled:

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.SITE_MAINTENANCE:
            return None

        template = loader.get_template('index.html')
        template_args = {
            'content': 'service/maintenance.html',
            'maintenance_over': settings.SITE_MAINTENANCE_OVER
        }

        return HttpResponse(
            template.render(
                template_args,
                request
            ),
            status=503
        )
