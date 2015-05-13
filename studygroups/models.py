from django.db import models
from django.db.models.signals import post_init
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from s3direct.fields import S3DirectField

from studygroups.sms import send_message

import calendar
import datetime
import pytz

STUDY_GROUP_NAMES = [
    "The Riders",
    "The Master Minds of Mars",
    "The Efficiency Experts",
    "The Red Hawks",
    "The Bandits of Hell's Bend",
    "Apache Devils",
    "The Wizards of Venus",
    "Swords of Mars",
    "The Beasts of Tarzan",
    "Tarzan and the Castaways",
    "Pirates of Venus",
    "The People that Time Forgot",
    "The Eternal Lovers"
]


def _study_group_name():
    idx = 1 + StudyGroup.objects.count()
    num_names = len(STUDY_GROUP_NAMES)
    return ' '.join([STUDY_GROUP_NAMES[idx%num_names], "I"*(idx/num_names)])


class Course(models.Model):
    title = models.CharField(max_length=128)
    provider = models.CharField(max_length=256)
    link = models.URLField()
    image = S3DirectField(dest='imgs', blank=True)
    key = models.CharField(max_length=255, default='NOT SET')
    start_date = models.DateField()
    duration = models.CharField(max_length=128)
    prerequisite = models.TextField()
    time_required = models.CharField(max_length=128)
    caption = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title


class StudyGroup(models.Model):
    name = models.CharField(max_length=128, default=_study_group_name)
    course = models.ForeignKey('studygroups.Course')
    location = models.CharField(max_length=128)
    location_link = models.URLField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    day = models.CharField(max_length=128, choices=zip(calendar.day_name, calendar.day_name))
    time = models.TimeField()
    duration = models.IntegerField()
    timezone = models.CharField(max_length=128)
    max_size = models.IntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def end_time(self):
        q = datetime.datetime.combine(timezone.now().date(), self.time) + datetime.timedelta(minutes=self.duration)
        return q.time()

    def __unicode__(self):
        return u'{0} - {1}s {2} at the {3}'.format(self.course.title, self.day, self.time, self.location)

#TODO - remove Text or Phone
PREFERRED_CONTACT_METHOD = [
    ('Email', 'Email'),
    ('Text', 'Text'),
]

COMPUTER_ACCESS = [
    ('No', 'No'),
    ('Sometimes', 'Sometimes'),
    ('Yes', 'Yes'),
]


class Application(models.Model):
    study_group = models.ForeignKey('studygroups.StudyGroup')
    name = models.CharField(max_length=128)
    contact_method = models.CharField(max_length=128, choices=PREFERRED_CONTACT_METHOD)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    computer_access = models.CharField(max_length=128, choices=COMPUTER_ACCESS)
    goals = models.TextField()
    support = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.name)


class Reminder(models.Model):
    study_group = models.ForeignKey('studygroups.StudyGroup')
    meeting_time = models.DateTimeField(blank=True, null=True)
    email_subject = models.CharField(max_length=256)
    email_body = models.TextField()
    sms_body = models.CharField(max_length=160)

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)


def accept_application(application):
    # add a study group application to a study group
    application.accepted_at = timezone.now()
    application.save()


def next_meeting_date(study_group):
    now = timezone.now()
    day_delta = list(calendar.day_name).index(study_group.day) - now.weekday()
    time = study_group.time
    date = now + datetime.timedelta(days=day_delta)
    tz = pytz.timezone(study_group.timezone)
    meeting_datetime = tz.localize(datetime.datetime(
        date.year, date.month, date.day,
        time.hour, time.minute
    ))
    if meeting_datetime < now:
        meeting_datetime = meeting_datetime + datetime.timedelta(weeks=1)

    if meeting_datetime < study_group.start_date or meeting_datetime > study_group.end_date:
        return None
    return meeting_datetime


def generate_reminder(study_group):
    now = timezone.now()
    next_meeting = next_meeting_date(study_group)
    if next_meeting and next_meeting - now < datetime.timedelta(days=3):
        # check if a notifcation already exists for this meeting
        if not Reminder.objects.filter(study_group=study_group, meeting_time=next_meeting).exists():
            reminder = Reminder()
            reminder.study_group = study_group
            reminder.meeting_time = next_meeting
            context = { 
                'study_group': study_group,
                'next_meeting': next_meeting,
                'reminder': reminder
            }
            timezone.activate(pytz.timezone(study_group.timezone))
            reminder.email_subject = render_to_string(
                'studygroups/notifications/reminder-subject.txt',
                context
            )
            reminder.email_body = render_to_string(
                'studygroups/notifications/reminder.html',
                context
            )
            reminder.sms_body = render_to_string(
                'studygroups/notifications/sms.txt',
                context
            )
            reminder.save()
            
            organizer_notification_subject = u'A reminder for {0} was generated'.format(study_group.course.title)
            organizer_notification = render_to_string(
                'studygroups/notifications/reminder-notification.html',
                context
            )
            timezone.deactivate()
            # TODO send email to study group organizer!
            to = [ a[1] for a in settings.ADMINS ]
            to += [settings.DEFAULT_FROM_EMAIL]
            send_mail(
                organizer_notification_subject,
                organizer_notification,
                settings.SERVER_EMAIL,
                to,
                fail_silently=False
            )


def send_group_message(study_group, email_subject, email_body, sms_body):
    to = [su.email for su in study_group.application_set.filter(accepted_at__isnull=False, contact_method='Email')]
    send_mail(email_subject.strip('\n'), email_body, settings.DEFAULT_FROM_EMAIL, to, fail_silently=False)

    # send SMS
    tos = [su.mobile for su in study_group.application_set.filter(accepted_at__isnull=False, contact_method='Text')]
    errors = []
    for to in tos:
        try:
            send_message(to, sms_body)
        except twilio.TwilioRestException as e:
            errors.push[e]
    if len(errors):
        raise Exception(errors)


def send_reminder(reminder):
    send_group_message(
        reminder.study_group,
        reminder.email_subject,
        reminder.email_body,
        reminder.sms_body
    )
    reminder.sent_at = timezone.now()
    reminder.save()
