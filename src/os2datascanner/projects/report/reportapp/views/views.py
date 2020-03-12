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
import structlog

from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView

from ..models.documentreport_model import DocumentReport
from ..models.roles.defaultrole_model import DefaultRole

from os2datascanner.engine2.rules.rule import Sensitivity

logger = structlog.get_logger()


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
    data_results = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # First attempt to make some usefull logging.
        # The report module task is to log every action the user makes
        # for the security of the user.
        # If the system can document the users actions the user can defend
        # them self against any allegations of wrong doing.
        logger.info('{} is watching {}.'.format(user, self.template_name))

        roles = user.roles.select_subclasses() or [DefaultRole(user=user)]
        results = DocumentReport.objects.none()
        for role in roles:
            results |= role.filter(DocumentReport.objects.all())
        self.data_results = results

        # Results are grouped by the rule they where found with,
        # together with the count.
        sensitivities = {}
        for dr in self.data_results:
            if dr.matches:
                print(dr.matches)
                sensitivity = dr.matches.sensitivity
                if not sensitivity in sensitivities:
                    sensitivities[sensitivity] = 0
                sensitivities[sensitivity] += 1
        context['dashboard_results'] = sensitivities

        return context


class SensitivityPageView(MainPageView):
    template_name = 'sensitivity.html'

    def get_context_data(self, **kwargs):
        sensitivity = Sensitivity(int(self.request.GET.get('value')) or 0)

        context = super().get_context_data(**kwargs)
        context['matches'] = [r for r in self.data_results
                if r.matches and r.matches.sensitivity == sensitivity]
        context['sensitivity'] = sensitivity

        return context


class ApprovalPageView(TemplateView):
    template_name = 'approval.html'


class StatsPageView(TemplateView):
    template_name = 'stats.html'


class SettingsPageView(TemplateView):
    template_name = 'settings.html'


class AboutPageView(TemplateView):
    template_name = 'about.html'
