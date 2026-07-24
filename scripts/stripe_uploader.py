#!/usr/bin/env python3
import os
import sys
import json
import stripe
from pricing import get_price_cents

HERE = os.path.dirname(os.path.abspath(__file__))
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# ... rest of your script