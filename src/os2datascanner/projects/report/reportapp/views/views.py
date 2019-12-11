import os
import json
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView


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
