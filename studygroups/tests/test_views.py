# coding: utf-8
from django.test import TestCase, override_settings
from django.test import Client
from django.core import mail
from django.contrib.auth.models import User
from django.utils import timezone

from mock import patch

from studygroups.models import StudyGroup
from studygroups.models import StudyGroupMeeting
from studygroups.models import Application
from studygroups.models import Rsvp
from studygroups.rsvp import gen_rsvp_querystring

import datetime

# Create your tests here.
class TestSignupViews(TestCase):

    fixtures = ['test_courses.json', 'test_studygroups.json']

    APPLICATION_DATA = {
        'name': 'Test User',
        'contact_method': Application.EMAIL,
        'email': 'test@mail.com',
        'computer_access': 'Yes', 
        'goals': 'try hard',
        'support': 'thinking how to?',
        'study_group': '1',
    }

    def setUp(self):
        user = User.objects.create_user('admin', 'admin@test.com', 'password')
        user.is_superuser = True
        user.is_staff = True
        user.save()


    def test_submit_application(self):
        c = Client()
        resp = c.post('/en/signup/foo-bob-1/', self.APPLICATION_DATA)
        self.assertRedirects(resp, '/en/signup/1/success/')
        self.assertEquals(Application.objects.all().count(), 1)
        # Make sure notification was sent 
        self.assertEqual(len(mail.outbox), 1)


    def test_update_application(self):
        c = Client()
        resp = c.post('/en/signup/foo-bob-1/', self.APPLICATION_DATA)
        self.assertRedirects(resp, '/en/signup/1/success/')
        self.assertEquals(Application.objects.all().count(), 1)
        # Make sure notification was sent 
        self.assertEqual(len(mail.outbox), 1)

        resp = c.post('/en/signup/foo-bob-1/', self.APPLICATION_DATA)
        self.assertRedirects(resp, '/en/signup/1/success/')
        self.assertEquals(Application.objects.all().count(), 1)
        
        data = self.APPLICATION_DATA.copy()
        data['email'] = 'test2@mail.com'
        resp = c.post('/en/signup/foo-bob-1/', data)
        self.assertRedirects(resp, '/en/signup/1/success/')
        self.assertEquals(Application.objects.all().count(), 2)

    
    @patch('studygroups.models.send_message')
    def test_send_email(self, send_message):
        # Test sending a message
        c = Client()
        c.login(username='admin', password='password')
        signup_data = self.APPLICATION_DATA.copy()
        signup_data['study_group'] = StudyGroup.objects.all()[0]
        signup = Application(**signup_data)
        signup.accepted_at = timezone.now()
        signup.save()
        url = '/en/studygroup/{0}/message/compose/'.format(signup.study_group_id)
        email_body = u'Hi there!\n\nThe first study group for GED® Prep Math will meet this Thursday, May 7th, from 6:00 pm - 7:45 pm at Edgewater on the 2nd floor. Feel free to bring a study buddy!\nFor any questions you can contact Emily at emily@p2pu.org.\n\nSee you soon'
        mail_data = {
            u'study_group': signup.study_group_id,
            u'email_subject': u'GED® Prep Math study group meeting Thursday 7 May 6:00 PM at Edgewater', 
            u'email_body': email_body, 
            u'sms_body': 'The first study group for GED® Prep Math will meet next Thursday, May 7th, from 6:00 pm-7:45 pm at Edgewater on the 2nd floor. Feel free to bring a study buddy!'
        }
        resp = c.post(url, mail_data)
        self.assertRedirects(resp, '/en/facilitator/')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, mail_data['email_subject'])
        self.assertFalse(send_message.called)


    @patch('studygroups.models.send_message')
    def test_send_sms(self, send_message):
        c = Client()
        c.login(username='admin', password='password')
        signup_data = self.APPLICATION_DATA.copy()
        signup_data['contact_method'] = Application.TEXT
        signup_data['mobile'] = '123-456-7890'
        signup_data['study_group'] = StudyGroup.objects.all()[0]
        signup = Application(**signup_data)
        signup.accepted_at = timezone.now()
        signup.save()
        url = '/en/studygroup/{0}/message/compose/'.format(signup.study_group_id)
        mail_data = {
            'study_group': signup.study_group_id,
            'email_subject': 'test', 
            'email_body': 'Email body', 
            'sms_body': 'Sms body'
        }
        resp = c.post(url, mail_data)
        self.assertRedirects(resp, '/en/facilitator/')
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(send_message.called)


    @patch('studygroups.models.send_message')
    def test_dont_send_email_to_unaccepted_signup(self, send_message):
        # Test sending a message
        c = Client()
        c.login(username='admin', password='password')
        signup_data = self.APPLICATION_DATA.copy()
        signup_data['study_group'] = StudyGroup.objects.all()[0]
        signup = Application(**signup_data)
        signup.save()
        url = '/en/studygroup/{0}/message/compose/'.format(signup.study_group_id)
        email_body = u'Hi there!\n\nThe first study group for GED® Prep Math will meet this Thursday, May 7th, from 6:00 pm - 7:45 pm at Edgewater on the 2nd floor. Feel free to bring a study buddy!\nFor any questions you can contact Emily at emily@p2pu.org.\n\nSee you soon'
        mail_data = {
            u'study_group': signup.study_group_id,
            u'email_subject': u'GED® Prep Math study group meeting Thursday 7 May 6:00 PM at Edgewater', 
            u'email_body': email_body, 
            u'sms_body': 'The first study group for GED® Prep Math will meet next Thursday, May 7th, from 6:00 pm-7:45 pm at Edgewater on the 2nd floor. Feel free to bring a study buddy!'
        }
        resp = c.post(url, mail_data)
        self.assertRedirects(resp, '/en/facilitator/')
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(send_message.called)


    def test_receive_sms(self):
        # Test sending a message
        signup_data = self.APPLICATION_DATA.copy()
        signup_data['contact_method'] = 'Text'
        signup_data['mobile'] = '123-456-7890'
        signup_data['study_group'] = StudyGroup.objects.all()[0]
        signup = Application(**signup_data)
        signup.accepted_at = timezone.now()
        signup.save()

        c = Client()
        url = '/en/receive_sms/'
        sms_data = {
            u'Body': 'The first study group for GED® Prep Math will meet next Thursday, May 7th, from 6:00 pm-7:45 pm at Edgewater on the 2nd floor. Feel free to bring a study buddy!',
            u'From': '+11234567890'
        }
        resp = c.post(url, sms_data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].subject.find('123-456-7890') > 0)
        self.assertTrue(mail.outbox[0].subject.find('Test User') > 0)
        self.assertIn(StudyGroup.objects.all()[0].facilitator.email, mail.outbox[0].to)


    def test_user_forbidden(self):
        user = User.objects.create_user('bob', 'bob@example.net', 'password')
        c = Client()
        c.login(username='bob', password='password')
        def assertAllowed(url):
            resp = c.get(url)
            self.assertTrue(resp.status_code, 403)
        assertAllowed('/en/studygroup/1/')
        assertAllowed('/en/studygroup/1/edit/')
        assertAllowed('/en/studygroup/1/message/compose/')
        assertAllowed('/en/studygroup/1/message/edit/1/')
        assertAllowed('/en/studygroup/1/message/list/')
        assertAllowed('/en/studygroup/1/member/add/')
        assertAllowed('/en/studygroup/1/member/2/delete/')
        assertAllowed('/en/studygroup/1/meeting/create/')
        assertAllowed('/en/studygroup/1/meeting/2/edit/')
        assertAllowed('/en/studygroup/1/meeting/2/delete/')
        assertAllowed('/en/studygroup/1/meeting/2/feedback/create/')


    def test_facilitator_access(self):
        User.objects.create_user('bob123', 'bob@example.net', 'password')
        user = User.objects.get(username='bob123')
        sg = StudyGroup.objects.get(pk=1)
        sg.facilitator = user
        sg.save()
        c = Client()
        c.login(username='bob123', password='password')
        def assertAllowed(url):
            resp = c.get(url)
            self.assertNotEqual(resp.status_code, 403)
        assertAllowed('/en/studygroup/1/')
        assertAllowed('/en/studygroup/1/edit/')
        assertAllowed('/en/studygroup/1/message/compose/')
        assertAllowed('/en/studygroup/1/message/edit/1/')
        assertAllowed('/en/studygroup/1/message/list/')
        assertAllowed('/en/studygroup/1/member/add/')
        assertAllowed('/en/studygroup/1/member/2/delete/')
        assertAllowed('/en/studygroup/1/meeting/create/')
        assertAllowed('/en/studygroup/1/meeting/2/edit/')
        assertAllowed('/en/studygroup/1/meeting/2/delete/')
        assertAllowed('/en/studygroup/1/meeting/2/feedback/create/')


    def test_rsvp_view(self):
        # Setup data for RSVP -> StudyGroup + Signup + Meeting in future

        study_group = StudyGroup.objects.all()[0]
        meeting_time = timezone.now() + datetime.timedelta(days=2)
        study_group_meeting = StudyGroupMeeting(
            study_group=study_group,
            meeting_time=meeting_time
        )
        study_group_meeting.save()

        signup_data = self.APPLICATION_DATA.copy()
        signup_data['study_group'] = study_group
        signup = Application(**signup_data)
        signup.accepted_at = timezone.now()
        signup.save()

        qs = gen_rsvp_querystring(
            signup.email,
            study_group.pk,
            study_group_meeting.meeting_time,
            'yes'
        )
        url = '/en/rsvp/?{0}'.format(qs)

        # Generate RSVP link
        # visit link
        c = Client()
        self.assertEqual(0, Rsvp.objects.count())
        resp = c.get(url)
        self.assertEqual(1, Rsvp.objects.count())
        self.assertTrue(Rsvp.objects.first().attending)

        qs = gen_rsvp_querystring(
            signup.email,
            study_group.pk,
            study_group_meeting.meeting_time,
            'no'
        )
        url = '/en/rsvp/?{0}'.format(qs)
        resp = c.get(url)
        self.assertEqual(1, Rsvp.objects.count())
        self.assertFalse(Rsvp.objects.first().attending)

