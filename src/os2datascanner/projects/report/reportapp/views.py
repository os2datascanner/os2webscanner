import os
import json
from django.views.generic import TemplateView


class LoginPageView(TemplateView):
    template_name = 'login.html'


class MainPageView(TemplateView):
    template_name = 'index.html'

class RulePageView(TemplateView):
    template_name = 'rule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/results-and-metadata.json','r') as fp:
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
