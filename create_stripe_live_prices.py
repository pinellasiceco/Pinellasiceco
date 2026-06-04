#!/usr/bin/env python3
"""
Run this locally with your Stripe live secret key:
  STRIPE_SECRET_KEY=sk_live_... python3 create_stripe_live_prices.py

Prints the live price IDs to paste back into stripe-checkout/index.ts.
"""
import os, urllib.request, urllib.parse, json

KEY = os.environ.get('STRIPE_SECRET_KEY', '')
if not KEY.startswith('sk_live_'):
    raise SystemExit('Set STRIPE_SECRET_KEY=sk_live_... before running')

def stripe_post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f'https://api.stripe.com/v1/{path}',
        data=body,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def make_price(name, amount_cents, recurring=None, desc=''):
    prod = stripe_post('products', {'name': name, 'description': desc or name})
    pid = prod['id']
    price_data = {'product': pid, 'currency': 'usd', 'unit_amount': amount_cents}
    if recurring:
        price_data['recurring[interval]'] = 'month'
    price = stripe_post('prices', price_data)
    return price['id']

print('Creating live Stripe products and prices...\n')

ids = {
    'entry_fee':             make_price('PIC Entry Fee',                  9900,                desc='$99 initial deep clean'),
    'monthly_base':          make_price('PIC Monthly Plan',               14900, recurring=True, desc='$149/mo base'),
    'quarterly_base':        make_price('PIC Quarterly Plan',             12900, recurring=True, desc='$129/mo base'),
    'monthly_additional':    make_price('PIC Monthly Additional Machine',  6900, recurring=True, desc='$69/mo per extra machine'),
    'quarterly_additional':  make_price('PIC Quarterly Additional Machine',4900, recurring=True, desc='$49/mo per extra machine'),
    'onetime_base':          make_price('PIC One-Time Service',           39500,                desc='$395 one-time'),
    'onetime_additional':    make_price('PIC One-Time Additional Machine',15000,                desc='$150 per extra machine'),
    'reach_in_monthly':      make_price('PIC Reach-In Monthly Add-On',    5000, recurring=True, desc='$50/mo reach-in cooler'),
    'reach_in_quarterly':    make_price('PIC Reach-In Quarterly Add-On',  4000, recurring=True, desc='$40/mo reach-in cooler'),
}

print('Done! Paste these into stripe-checkout/index.ts:\n')
print('const STRIPE_PRICES = {')
for k, v in ids.items():
    print(f"  {k+':':<26} '{v}',")
print('};')
