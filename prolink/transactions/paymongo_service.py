"""
PayMongo Payment Integration Service
Handles checkout sessions, payment links, and webhooks
"""
import base64
import json
from urllib import request as urlrequest
from urllib import error as urlerror
from django.conf import settings
from decimal import Decimal


class PayMongoService:
    """Service class for PayMongo API integration"""
    
    BASE_URL = "https://api.paymongo.com/v1"
    
    def __init__(self):
        self.secret_key = settings.PAYMONGO_SECRET_KEY
        self.public_key = settings.PAYMONGO_PUBLIC_KEY
        self.test_mode = settings.PAYMONGO_TEST_MODE
        
        # Create auth header
        auth_string = f"{self.secret_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
    
    def create_checkout_session(self, transaction, success_url, cancel_url):
        """
        Create a PayMongo checkout session
        
        Args:
            transaction: Transaction model instance
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            dict: Checkout session data with checkout_url
        """
        amount_centavos = int(transaction.amount * 100)  # Convert to centavos
        
        payload = {
            "data": {
                "attributes": {
                    "send_email_receipt": True,
                    "show_description": True,
                    "show_line_items": True,
                    "description": f"Payment for: {transaction.request.title}",
                    "line_items": [
                        {
                            "currency": "PHP",
                            "amount": amount_centavos,
                            "description": transaction.request.title,
                            "name": f"Service Request #{transaction.request.id}",
                            "quantity": 1
                        }
                    ],
                    "payment_method_types": [
                        "gcash",
                        "grab_pay",
                        "paymaya",
                        "card"
                    ],
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "metadata": {
                        "transaction_id": str(transaction.id),
                        "request_id": str(transaction.request.id),
                        "client_id": str(transaction.client.id),
                        "professional_id": str(transaction.professional.id)
                    }
                }
            }
        }
        
        try:
            req = urlrequest.Request(
                url=f"{self.BASE_URL}/checkout_sessions",
                data=json.dumps(payload).encode('utf-8'),
                headers=self.headers,
                method='POST'
            )
            with urlrequest.urlopen(req, timeout=30) as resp:
                response_body = resp.read().decode('utf-8')
                data = json.loads(response_body)

            return {
                'success': True,
                'checkout_url': data['data']['attributes']['checkout_url'],
                'checkout_id': data['data']['id'],
                'data': data
            }

        except (urlerror.HTTPError, urlerror.URLError, Exception) as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create checkout session'
            }
    
    def retrieve_checkout_session(self, checkout_id):
        """
        Retrieve checkout session details
        
        Args:
            checkout_id: PayMongo checkout session ID
            
        Returns:
            dict: Session data including payment status
        """
        try:
            req = urlrequest.Request(
                url=f"{self.BASE_URL}/checkout_sessions/{checkout_id}",
                headers=self.headers,
                method='GET'
            )
            with urlrequest.urlopen(req, timeout=30) as resp:
                response_body = resp.read().decode('utf-8')
                data = json.loads(response_body)
            return data

        except (urlerror.HTTPError, urlerror.URLError, Exception) as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, checkout_id):
        """
        Get payment status from checkout session
        
        Returns:
            str: 'paid', 'unpaid', or 'expired'
        """
        session = self.retrieve_checkout_session(checkout_id)
        # If retrieval failed
        if isinstance(session, dict) and session.get('success') is False:
            return 'error'

        # Happy path: top-level payment_status field
        attributes = (session or {}).get('data', {}).get('attributes', {}) if isinstance(session, dict) else {}
        payment_status = attributes.get('payment_status')
        if payment_status in ('paid', 'unpaid', 'expired'):
            return payment_status

        # Fallbacks: inspect payments array if present
        payments = attributes.get('payments') or []
        if isinstance(payments, list) and payments:
            try:
                first_payment = payments[0]
                fp_attr = first_payment.get('attributes', {})
                if fp_attr.get('status') == 'paid' or fp_attr.get('paid_at'):
                    return 'paid'
            except Exception:
                pass

        # Fallback: inspect embedded payment_intent if present
        payment_intent = attributes.get('payment_intent', {})
        if isinstance(payment_intent, dict):
            pi_attr = payment_intent.get('attributes', {})
            if pi_attr.get('status') == 'succeeded':
                return 'paid'

        return 'unpaid'
    
    def create_payment_intent(self, amount, description, metadata=None):
        """
        Create a payment intent (alternative to checkout session)
        
        Args:
            amount: Amount in PHP (will be converted to centavos)
            description: Payment description
            metadata: Additional data to attach
            
        Returns:
            dict: Payment intent data
        """
        amount_centavos = int(Decimal(amount) * 100)
        
        payload = {
            "data": {
                "attributes": {
                    "amount": amount_centavos,
                    "payment_method_allowed": [
                        "gcash",
                        "grab_pay",
                        "paymaya",
                        "card"
                    ],
                    "payment_method_options": {
                        "card": {
                            "request_three_d_secure": "any"
                        }
                    },
                    "currency": "PHP",
                    "description": description,
                    "statement_descriptor": "ProLink",
                    "metadata": metadata or {}
                }
            }
        }
        
        try:
            req = urlrequest.Request(
                url=f"{self.BASE_URL}/payment_intents",
                data=json.dumps(payload).encode('utf-8'),
                headers=self.headers,
                method='POST'
            )
            with urlrequest.urlopen(req, timeout=30) as resp:
                response_body = resp.read().decode('utf-8')
                data = json.loads(response_body)
            return data

        except (urlerror.HTTPError, urlerror.URLError, Exception) as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature from PayMongo
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            
        Returns:
            bool: True if signature is valid
        """
        # TODO: Implement signature verification
        # For now, we'll skip verification in test mode
        if self.test_mode:
            return True
        
        # In production, verify using webhook secret
        return True
    
    @staticmethod
    def get_test_card_numbers():
        """
        Get PayMongo test card numbers for testing
        
        Returns:
            dict: Test card numbers and their behaviors
        """
        return {
            'success': {
                'number': '4343434343434345',
                'cvc': '123',
                'exp_month': '12',
                'exp_year': '25',
                'description': 'Successful payment'
            },
            'declined': {
                'number': '4571736000000075',
                'cvc': '123',
                'exp_month': '12',
                'exp_year': '25',
                'description': 'Payment declined'
            },
            'insufficient_funds': {
                'number': '4571736000000067',
                'cvc': '123',
                'exp_month': '12',
                'exp_year': '25',
                'description': 'Insufficient funds'
            }
        }
    
    @staticmethod
    def get_test_gcash_info():
        """
        Get test GCash information for testing
        
        Returns:
            dict: Test GCash details
        """
        return {
            'message': 'In test mode, you can use any phone number for GCash',
            'phone': '09123456789',
            'note': 'Payment will be marked as successful automatically in test mode'
        }
