from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from .models import Audit, Review
from .scanner import validate_url

@override_settings(SECURE_SSL_REDIRECT=False,SCANNER_ENABLED=True,EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ApplicationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=get_user_model().objects.create_user('ana',password='Example-strong-875!')
        self.other=get_user_model().objects.create_user('bea',password='Example-strong-875!')
        self.audit=Audit.objects.create(owner=self.user,url='https://example.com')
        self.review=Review.objects.create(audit=self.audit,criterion='rights')
    def test_login_required(self):
        self.assertEqual(self.client.get('/').status_code,302)
    def test_owner_dashboard_detail_pdf(self):
        self.client.force_login(self.user)
        for url in ('/',f'/auditoria/{self.audit.pk}/','/nueva/','/privacidad/'):
            self.assertEqual(self.client.get(url).status_code,200)
        response=self.client.get(f'/auditoria/{self.audit.pk}/pdf/')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.content.startswith(b'%PDF'))
    def test_other_user_cannot_access_modify_send_delete(self):
        self.client.force_login(self.other)
        for suffix in ('','pdf/'):
            self.assertEqual(self.client.get(f'/auditoria/{self.audit.pk}/{suffix}').status_code,404)
        for suffix in ('','enviar/','eliminar/'):
            self.assertEqual(self.client.post(f'/auditoria/{self.audit.pk}/{suffix}',{}).status_code,404)
        self.assertTrue(Audit.objects.filter(pk=self.audit.pk).exists())
    def test_admin_can_access_all(self):
        self.other.is_staff=True; self.other.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/auditoria/{self.audit.pk}/').status_code,200)
    @patch('audits.views.scan',return_value=[])
    def test_create_audit_generates_manual_criteria(self,scan):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/nueva/',{'url':'https://example.org','authorization':'on'}).status_code,302)
        self.assertEqual(Audit.objects.get(url='https://example.org').reviews.count(),9)
        self.client.post('/nueva/',{'url':'https://example.net','authorization':'on'})
        self.assertEqual(scan.call_count,1)
    def test_send_attaches_real_pdf(self):
        self.client.force_login(self.user)
        response=self.client.post(f'/auditoria/{self.audit.pk}/enviar/',{'recipient':'recipient@example.org','confirm':'on'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(len(mail.outbox),1)
        self.assertTrue(mail.outbox[0].attachments[0][1].startswith(b'%PDF'))
    def test_manual_evidence_persists(self):
        self.client.force_login(self.user)
        response=self.client.post(f'/auditoria/{self.audit.pk}/',{'form-TOTAL_FORMS':'1','form-INITIAL_FORMS':'1','form-MIN_NUM_FORMS':'0','form-MAX_NUM_FORMS':'1000','form-0-id':str(self.review.pk),'form-0-status':'yes','form-0-evidence':'Procedimiento revisado con responsable.'})
        self.assertEqual(response.status_code,302)
        self.review.refresh_from_db(); self.assertEqual(self.review.status,'yes')
    def test_csrf_protection(self):
        from django.test import Client
        client=Client(enforce_csrf_checks=True); client.force_login(self.user)
        self.assertEqual(client.post(f'/auditoria/{self.audit.pk}/eliminar/').status_code,403)
    def test_private_ip_rejected(self):
        for url in ('http://127.0.0.1','http://169.254.169.254','http://[::1]','ftp://example.com','https://user:password@example.com','https://example.com:8080'):
            with self.assertRaises(ValueError): validate_url(url)

    @override_settings(SCANNER_ENABLED=False)
    @patch('audits.views.scan')
    def test_production_scanner_disabled_by_default(self,scan):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/nueva/',{'url':'https://example.org','authorization':'on'}).status_code,200)
        scan.assert_not_called()

    def test_cannot_change_other_review_through_formset(self):
        other_audit=Audit.objects.create(owner=self.other,url='https://example.org')
        other_review=Review.objects.create(audit=other_audit,criterion='rights')
        self.client.force_login(self.user)
        self.client.post(f'/auditoria/{self.audit.pk}/',{'form-TOTAL_FORMS':'1','form-INITIAL_FORMS':'1','form-MIN_NUM_FORMS':'0','form-MAX_NUM_FORMS':'1000','form-0-id':str(other_review.pk),'form-0-status':'yes','form-0-evidence':'Alterado'})
        other_review.refresh_from_db()
        self.assertEqual(other_review.status,'pending')


@override_settings(SECURE_SSL_REDIRECT=False)
class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.data = {'username': 'nuevo', 'password1': 'Long-unique-Password-683!', 'password2': 'Long-unique-Password-683!'}

    def test_register_page_and_login_link(self):
        self.assertContains(self.client.get('/registro/'), 'Crear cuenta')
        self.assertContains(self.client.get('/cuentas/login/'), '/registro/')

    def test_create_normal_account_and_login(self):
        response = self.client.post('/registro/', {**self.data, 'is_staff': 'on', 'is_superuser': 'on'})
        self.assertRedirects(response, '/cuentas/login/')
        user = get_user_model().objects.get(username='nuevo')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.data['password1']))
        self.assertTrue(self.client.login(username='nuevo', password=self.data['password1']))
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_reject_invalid_passwords_and_duplicates(self):
        for data in ({**self.data, 'password2': 'different'}, {**self.data, 'password1': '123', 'password2': '123'}):
            self.assertEqual(self.client.post('/registro/', data).status_code, 200)
        self.assertFalse(get_user_model().objects.exists())
        self.client.post('/registro/', self.data)
        self.assertEqual(self.client.post('/registro/', self.data).status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.client.post('/registro/', {}).status_code, 200)
        response = self.client.post('/registro/', self.data)
        self.assertEqual(response.status_code, 429)
        self.assertFalse(get_user_model().objects.exists())

    def test_registration_csrf_required(self):
        from django.test import Client
        self.assertEqual(Client(enforce_csrf_checks=True).post('/registro/', self.data).status_code, 403)

    def test_authenticated_user_redirects(self):
        user = get_user_model().objects.create_user('existente', password='Example-strong-875!')
        self.client.force_login(user)
        self.assertRedirects(self.client.get('/registro/'), '/')
