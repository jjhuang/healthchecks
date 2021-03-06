from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from hc.accounts.models import Profile
from hc.api.models import Check


def num_pinged_checks(profile):
    q = Check.objects.filter(user_id=profile.user.id,)
    q = q.filter(last_ping__isnull=False)
    return q.count()


class Command(BaseCommand):
    help = 'Send due monthly reports'
    tmpl = "Sending monthly report to %s"

    def handle(self, *args, **options):
        now = timezone.now()
        month_before = now - timedelta(days=30)

        report_due = Q(next_report_date__lt=now)
        report_not_scheduled = Q(next_report_date__isnull=True)

        q = Profile.objects.filter(report_due | report_not_scheduled)
        q = q.filter(reports_allowed=True)
        q = q.filter(user__date_joined__lt=month_before)
        sent = 0
        for profile in q:
            if num_pinged_checks(profile) > 0:
                self.stdout.write(self.tmpl % profile.user.email)
                profile.send_report()
                sent += 1

        return "Sent %d reports" % sent
