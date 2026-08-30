from decimal import Decimal
import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from account.models import User

from .models import (
    Invoice,
    PaymentWebhookLog,
    SubscriptionPlan,
    UserSubscription,
)


@override_settings(
    RAZORPAY_KEY_ID='rzp_test_key',
    RAZORPAY_KEY_SECRET='rzp_test_secret',
)
class RazorpaySubscriptionTests(TestCase):
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name='Monthly News',
            subscription_type='news',
            price=Decimal('99.00'),
            duration=1,
            duration_type='months',
            description='Monthly premium news access',
        )
        self.yearly_plan = SubscriptionPlan.objects.create(
            name='Yearly News',
            subscription_type='news',
            price=Decimal('500.00'),
            duration=1,
            duration_type='years',
            description='Yearly premium news access',
        )
        self.reporter = User.objects.create_user(
            username='reporter@example.com',
            email='reporter@example.com',
            mobile='9000000000',
            user_type='reporter',
            password='secret123',
        )
        self.subscriber = User.objects.create_user(
            username='subscriber@example.com',
            email='subscriber@example.com',
            mobile='9111111111',
            full_name='Old Subscriber',
            address='Old Address',
            city='Old City',
            state='Uttar Pradesh',
            pincode='111111',
            country='India',
            user_type='subscriber',
            password='secret123',
        )

    def test_create_order_clears_selected_subscriber_session(self):
        self.client.force_login(self.reporter)
        session = self.client.session
        session['subscription_customer_id'] = self.subscriber.id
        session['reporter_mobile'] = self.reporter.mobile
        session.save()

        razorpay_response = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    'id': 'order_test_123',
                    'amount': 9900,
                    'currency': 'INR',
                }
            )
        )

        with patch('subscriptions.views.requests.post', return_value=razorpay_response):
            response = self.client.post(
                reverse('razorpay_create_order', args=[self.plan.id]),
                {'reporter_mobile': self.reporter.mobile}
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'subscription_customer_id',
            self.client.session
        )
        self.assertNotIn('reporter_mobile', self.client.session)
        self.assertTrue(
            UserSubscription.objects.filter(
                user=self.subscriber,
                transaction_id='order_test_123',
                payment_status='PENDING',
            ).exists()
        )

    def test_different_plan_clears_selected_subscriber_checkout_session(self):
        self.client.force_login(self.reporter)
        session = self.client.session
        session['subscription_customer_id'] = self.subscriber.id
        session['subscription_customer_plan_id'] = self.plan.id
        session['reporter_mobile'] = self.reporter.mobile
        session.save()

        response = self.client.get(
            reverse('subscribe', args=[self.yearly_plan.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'subscription_customer_id',
            self.client.session
        )
        self.assertNotIn(
            'subscription_customer_plan_id',
            self.client.session
        )
        self.assertNotIn('reporter_mobile', self.client.session)
        self.assertIsNone(response.context['subscription_customer'])
        self.assertTrue(response.context['show_account_form'])

    def test_same_plan_keeps_selected_subscriber_checkout_session(self):
        self.client.force_login(self.reporter)
        session = self.client.session
        session['subscription_customer_id'] = self.subscriber.id
        session['subscription_customer_plan_id'] = self.plan.id
        session['reporter_mobile'] = self.reporter.mobile
        session.save()

        response = self.client.get(reverse('subscribe', args=[self.plan.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['subscription_customer'],
            self.subscriber
        )
        self.assertFalse(response.context['show_account_form'])

    def test_invoice_syncs_latest_subscriber_details_on_success(self):
        subscription = UserSubscription.objects.create(
            user=self.subscriber,
            plan=self.plan,
            amount=self.plan.price,
            transaction_id='order_test_456',
            payment_status='PENDING',
        )
        invoice = Invoice.objects.create(
            subscription=subscription,
            invoice_number='GT-OLD',
            billing_name='Old Subscriber',
            billing_email='old@example.com',
            billing_mobile='9000000001',
            billing_address='Previous Address',
            billing_city='Previous City',
            billing_state='Delhi',
            billing_pincode='222222',
            billing_country='India',
            amount=Decimal('1.00'),
        )

        self.subscriber.full_name = 'New Subscriber'
        self.subscriber.email = 'new-subscriber@example.com'
        self.subscriber.mobile = '9222222222'
        self.subscriber.address = 'Fresh Address'
        self.subscriber.city = 'Fresh City'
        self.subscriber.state = 'Uttar Pradesh'
        self.subscriber.pincode = '333333'
        self.subscriber.save()

        from .views import mark_subscription_success

        mark_subscription_success(subscription)

        invoice.refresh_from_db()
        self.assertEqual(invoice.billing_name, 'New Subscriber')
        self.assertEqual(invoice.billing_email, 'new-subscriber@example.com')
        self.assertEqual(invoice.billing_mobile, '9222222222')
        self.assertEqual(invoice.billing_address, 'Fresh Address')
        self.assertEqual(invoice.billing_city, 'Fresh City')
        self.assertEqual(invoice.billing_pincode, '333333')
        self.assertEqual(invoice.amount, self.plan.price)

    def test_razorpay_callback_activates_only_captured_payment(self):
        subscription = UserSubscription.objects.create(
            user=self.subscriber,
            plan=self.plan,
            amount=self.plan.price,
            transaction_id='order_test_captured',
            razorpay_order_id='order_test_captured',
            payment_status='PENDING',
        )
        payment_id = 'pay_test_captured'
        signature = hmac.new(
            b'rzp_test_secret',
            f'{subscription.razorpay_order_id}|{payment_id}'.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch(
            'subscriptions.views.fetch_razorpay_payment',
            return_value={
                'id': payment_id,
                'order_id': subscription.razorpay_order_id,
                'status': 'captured',
                'captured': True,
                'method': 'upi',
                'currency': 'INR',
            }
        ):
            response = self.client.post(
                reverse('razorpay_payment_callback'),
                {
                    'razorpay_payment_id': payment_id,
                    'razorpay_order_id': subscription.razorpay_order_id,
                    'razorpay_signature': signature,
                }
            )

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.payment_status, 'SUCCESS')
        self.assertEqual(subscription.access_status, 'ACTIVE')
        self.assertTrue(subscription.is_active)
        self.assertEqual(subscription.razorpay_payment_id, payment_id)
        self.assertEqual(subscription.payment_method, 'upi')
        self.assertIsNotNone(subscription.activated_at)
        self.assertIsNotNone(subscription.delivered_at)
        self.assertTrue(hasattr(subscription, 'invoice'))

    def test_razorpay_callback_does_not_activate_authorized_payment(self):
        subscription = UserSubscription.objects.create(
            user=self.subscriber,
            plan=self.plan,
            amount=self.plan.price,
            transaction_id='order_test_authorized',
            razorpay_order_id='order_test_authorized',
            payment_status='PENDING',
        )
        payment_id = 'pay_test_authorized'
        signature = hmac.new(
            b'rzp_test_secret',
            f'{subscription.razorpay_order_id}|{payment_id}'.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch(
            'subscriptions.views.fetch_razorpay_payment',
            return_value={
                'id': payment_id,
                'order_id': subscription.razorpay_order_id,
                'status': 'authorized',
                'captured': False,
                'method': 'card',
                'currency': 'INR',
            }
        ):
            response = self.client.post(
                reverse('razorpay_payment_callback'),
                {
                    'razorpay_payment_id': payment_id,
                    'razorpay_order_id': subscription.razorpay_order_id,
                    'razorpay_signature': signature,
                }
            )

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.payment_status, 'AUTHORIZED')
        self.assertEqual(subscription.access_status, 'PENDING')
        self.assertFalse(subscription.is_active)
        self.assertEqual(subscription.razorpay_payment_id, payment_id)
        self.assertFalse(Invoice.objects.filter(subscription=subscription).exists())

    @override_settings(RAZORPAY_WEBHOOK_SECRET='webhook_secret')
    def test_duplicate_razorpay_webhook_is_ignored(self):
        subscription = UserSubscription.objects.create(
            user=self.subscriber,
            plan=self.plan,
            amount=self.plan.price,
            transaction_id='order_test_webhook',
            razorpay_order_id='order_test_webhook',
            payment_status='PENDING',
        )
        payload = {
            'id': 'evt_test_duplicate',
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_webhook',
                        'order_id': subscription.razorpay_order_id,
                        'status': 'captured',
                        'captured': True,
                        'method': 'netbanking',
                        'currency': 'INR',
                    }
                }
            }
        }
        raw_payload = json.dumps(payload).encode()
        signature = hmac.new(
            b'webhook_secret',
            raw_payload,
            hashlib.sha256
        ).hexdigest()

        for _ in range(2):
            response = self.client.post(
                reverse('razorpay_webhook'),
                data=raw_payload,
                content_type='application/json',
                HTTP_X_RAZORPAY_SIGNATURE=signature
            )
            self.assertEqual(response.status_code, 200)

        subscription.refresh_from_db()
        self.assertEqual(subscription.payment_status, 'SUCCESS')
        self.assertEqual(subscription.payment_method, 'netbanking')
        self.assertEqual(PaymentWebhookLog.objects.count(), 1)
