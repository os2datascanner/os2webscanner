import os
import json
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView

from ..models.documentreport_model import DocumentReport


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        return super().dispatch(*args, **kwargs)


class LoginPageView(View):
    template_name = 'login.html'


class MainPageView(TemplateView, LoginRequiredMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        aliases = user.aliases.select_subclasses()
        # user.aliases.select_subclasses().get().sid
        for alias in aliases:
            if alias.sid:
                print(alias.sid)
                # I wonder how this performs. It might be an idea to move the sid property to the RDB-schema.
                # Then we would just have to do DocumentReport.objects.filter(sid=alias.sid)...
                metadata_results = DocumentReport.objects.filter(
                    data__contains={'origin': 'os2ds_metadata'}).filter(
                    data__metadata__contains={'filesystem-owner-sid': alias.sid})
                for data in metadata_results:
                    matches_results = DocumentReport.objects.filter(
                        data__contains={'origin': 'os2ds_matches'}).filter(
                        data__handle__source__path=data.path)
                    context['matches'] = matches_results
            elif alias.address:
                print(alias.address)



class RulePageView(TemplateView):
    template_name = 'rule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/results-and-metadata.jsonl','r') as fp:
            lines = fp.readlines()
            json_list = []
            for line in lines:
                json_list.append(json.loads(line))
            context['hits'] = json_list

        print(type(context['hits'][0]))

        return context


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'
