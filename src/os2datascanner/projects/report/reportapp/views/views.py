#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )
from django.db.models import Count
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
    filedata_results = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        aliases = user.aliases.select_subclasses()
        for alias in aliases:
            if alias.sid:
                self.filedata_results = DocumentReport.objects.filter(
                    data__metadata__metadata__contains={
                        'filesystem-owner-sid': str(alias.sid)
                    })
            elif alias.address:
                # TODO: Find related email results.
                print(alias.address)

        # Results are grouped by the rule they where found with,
        # together with the count.
        context['dashboard_results'] = self.filedata_results.values(
            'data__matches__scan_spec__rule').annotate(
            type_count=Count('data__matches__scan_spec__rule'))

        return context


class RulePageView(MainPageView):
    template_name = 'rule.html'

    def get_context_data(self, **kwargs):
        type = self.request.GET.get('type')

        context = super().get_context_data(**kwargs)
        context['matches_by_type'] = self.filedata_results.filter(
            data__matches__scan_spec__rule__type=type)
        context['type'] = type

        return context


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'
