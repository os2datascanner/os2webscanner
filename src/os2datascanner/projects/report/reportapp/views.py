from django.views.generic import TemplateView


class LoginPageView(TemplateView):
    template_name = 'login.html'


class MainPageView(TemplateView):
    template_name = 'index.html'


class RulePageView(TemplateView):
    template_name = 'rule.html'


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'
