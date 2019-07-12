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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains Django views."""
import csv

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse

from .views import LoginRequiredMixin, RestrictedListView, \
    DeleteView, UpdateView
from ..models.match_model import Match
from ..models.referrerurl_model import ReferrerUrl
from ..models.scans.scan_model import Scan
from ..models.statistic_model import Statistic
from ..models.webversion_model import WebVersion
from ..models.userprofile_model import UserProfile


class ReportList(RestrictedListView):
    """Displays list of scanners."""

    model = Scan
    template_name = 'os2datascanner/reports.html'
    paginate_by = 15

    active = 'all'

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if self.queryset is not None:
            objects = self.queryset
        else:
            objects = self.model.objects.all()

        if user.is_superuser:
            reports = objects
        else:
            try:
                profile = user.profile
                # TODO: Filter by group here if relevant.
                if (
                        profile.is_group_admin or not
                        profile.organization.do_use_groups
                ):
                    reports = objects.filter(
                        scanner__organization=profile.organization
                    )
                else:
                    reports = objects.filter(
                        scanner__group__in=profile.groups.all()
                    )
            except UserProfile.DoesNotExist:
                reports = objects.filter(
                    scanner__organization=None
                )
        reports = reports.filter(is_visible=True)
        return reports.order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active'] = self.active
        return context


# Reports stuff
class ReportDetails(UpdateView, LoginRequiredMixin):
    """Display a detailed report summary."""

    model = Scan
    template_name = 'os2datascanner/report.html'
    context_object_name = "scan"
    full = False

    fields = '__all__'

    def get_queryset(self):
        """Get the queryset for the view.

        If the user is not a superuser the queryset will be limited by the
        user's organization.
        """
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.profile
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None
            queryset = queryset.filter(scanner__organization=organization)
        return queryset

    def get_context_data(self, **kwargs):
        """Add the scan's matches to the report context data."""
        this_scan = self.get_object()

        context = super().get_context_data(**kwargs)
        all_matches = Match.objects.filter(
            url__scan=this_scan
        ).order_by('-sensitivity', 'url', 'matched_rule', 'matched_data')

        broken_urls = WebVersion.objects.filter(
            scan=this_scan
        ).exclude(status_code__isnull=True).order_by('location__url')

        referrer_urls = ReferrerUrl.objects.filter(scan=this_scan)

        context['full_report'] = self.full
        context['broken_urls'] = broken_urls[:100]
        context['no_of_broken_links'] = broken_urls.count()
        context['referrer_urls'] = referrer_urls
        context['matches'] = all_matches[:100]
        context['all_matches'] = all_matches
        context['no_of_matches'] = all_matches.count() + broken_urls.count()
        context['failed_conversions'] = (
            this_scan.get_number_of_failed_conversions()
        )
        try:
            stats = Statistic.objects.get(scan=this_scan)
            context['files_scraped_count'] = stats.files_scraped_count
            context['files_is_dir_count'] = stats.files_is_dir_count
            context['files_skipped_count'] = stats.files_skipped_count

            context["supported_size"] = stats.supported_size
            context["supported_count"] = stats.supported_count
            context["relevant_size"] = stats.relevant_size
            context["relevant_count"] = stats.relevant_count
            context["relevant_unsupported_size"] = \
                stats.relevant_unsupported_size
            context["relevant_unsupported_count"] = \
                stats.relevant_unsupported_count
        except ObjectDoesNotExist:
            pass

        return context


class ReportDelete(DeleteView, LoginRequiredMixin):
    """View for deleting a report."""

    model = Scan
    success_url = '/reports/'

    def get_queryset(self):
        """Get the queryset for the view.

        If the user is not a superuser the queryset will be limited by the
        user's organization.
        """
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.profile
                organization = user_profile.organization
            except UserProfile.DoesNotExist:
                organization = None
            queryset = queryset.filter(scanner__organization=organization)
        return queryset


class ScanReportLog(ReportDetails):
    """Display ordinary log file for debugging purposes."""

    def render_to_response(self, context, **response_kwargs):
        """Render log file."""
        scan = self.get_object()
        response = HttpResponse(content_type="text/plain")
        log_file = "scan{0}_log.txt".format(scan.id)
        response[
            'Content-Disposition'
        ] = 'attachment; filename={0}'.format(log_file)

        with open(scan.scan_log_file, "r") as f:
            response.write(f.read())
        return response


class Echo:
    def write(self, value):
        return value


def render_csv_report(scan, context):
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # CSV utilities
    # Print summary header
    yield writer.writerow([
            'Starttidspunkt', 'Sluttidspunkt', 'Status',
            'Totalt antal matches', 'Total antal broken links'])
    yield writer.writerow([
            scan.start_time, scan.end_time, scan.get_status_display(),
            context['no_of_matches'], context['no_of_broken_links']])

    all_matches = context['all_matches']
    if all_matches:
        # Print match header
        yield writer.writerow([
                'URL', 'Regel', 'Match', 'Følsomhed', 'Kontekst'])

        for match in all_matches:
            yield writer.writerow([
                    match.url.url, match.get_matched_rule_display(),
                    match.matched_data.replace('\n', '').replace('\r', ' '),
                    match.get_sensitivity_display(),
                    match.match_context])

    broken_urls = context['broken_urls']
    if broken_urls:
        # Print broken link header
        yield writer.writerow(['Referrers', 'URL', 'Status'])
        for url in broken_urls:
            for referrer in url.referrers.all():
                yield writer.writerow([
                        referrer.url, url.url, url.status_message])

class CSVReportDetails(ReportDetails):
    """Display full report in CSV format."""

    def render_to_response(self, context, **response_kwargs):
        """Generate a CSV file and return it as the http response."""
        scan = self.get_object()
        response = StreamingHttpResponse(
                render_csv_report(scan, context), content_type='text/csv')
        report_file = '{0}{1}.csv'.format(
            scan.scanner.organization.name.replace(' ', '_'),
            scan.id)
        response['Content-Disposition'] = (
                'attachment; filename={0}'.format(report_file))
        return response
