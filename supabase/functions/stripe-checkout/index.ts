import Stripe from 'https://esm.sh/stripe@14.21.0?target=deno';

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
  apiVersion: '2024-06-20',
  httpClient: Stripe.createFetchHttpClient(),
});

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers':
    'authorization, x-client-info, apikey, content-type',
};

// Reference price IDs — checkout uses dynamic price_data (computed per request)
const STRIPE_PRICES = {
  entry_fee:             'price_1TXrHM1DW5dOU2aay60IOPnW',   // $99 one-time
  monthly_base:          'price_1TXrIG1DW5dOU2aaqhWTDpHG',   // $149/mo
  quarterly_base:        'price_1TXrIu1DW5dOU2aacIeDByPC',   // $129/mo
  monthly_additional:    'price_1TXrZg1DW5dOU2aalDMRdtD1',   // $69/mo per extra machine
  quarterly_additional:  'price_1TXra61DW5dOU2aaOUH8FbBa',   // $49/mo per extra machine
  onetime_base:          'price_1TXrJQ1DW5dOU2aa4jQguT8b',   // $395 one-time
  onetime_additional:    'price_1TXral1DW5dOU2aaXB5myZ8O',   // $150 per extra machine
  reach_in_monthly:      'price_1TZDEZ1DW5dOU2aa40hWFQsm',   // $50/mo reach-in add-on
  reach_in_quarterly:    'price_1TZDF71DW5dOU2aaT1PYaOaw',   // $40/mo reach-in add-on
};

const TERMS_URL = 'https://www.pinellasiceco.com/terms';
const SUCCESS_BASE = 'https://pinellasiceco.github.io/Pinellasiceco/';
const CANCEL_URL   = 'https://pinellasiceco.github.io/Pinellasiceco/?stripe=cancel';

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const {
      plan,              // 'monthly' | 'quarterly' | 'onetime'
      machines,          // number, minimum 1
      entry_discount,    // dollar amount off entry fee (0 if none)
      monthly_discount,  // dollar amount off plan price (0 if none)
      client_name,       // business name
      client_email,      // optional — pre-fills checkout email field
      client_address,    // street address from P[] record
      client_city,       // city from P[] record
      prospect_id,       // for metadata/tracking and return URL
      flex,              // boolean — month-to-month terms if true
      reach_in,          // boolean — reach-in cooler add-on selected
    } = await req.json();

    if (!plan || !machines || Number(machines) < 1) {
      throw new Error('Invalid parameters: plan and machines required');
    }

    const m = Math.max(1, Math.round(Number(machines)));
    const extraMachines = Math.max(0, m - 1);
    const entryDisc = Math.max(0, Math.min(Number(entry_discount) || 0, 99));
    const planDisc  = Math.max(0, Number(monthly_discount) || 0);
    const hasReachIn = reach_in === true && plan !== 'onetime';

    // --- CREATE NAMED CUSTOMER ---
    const addressParts = [
      String(client_address || '').trim(),
      String(client_city || '').trim(),
      'FL',
    ].filter(Boolean);
    const customerDescription = addressParts.join(', ');

    const customerParams: Stripe.CustomerCreateParams = {
      name: String(client_name || '').trim() || 'Unknown',
      description: customerDescription,
      metadata: {
        prospect_id: String(prospect_id || ''),
        address: String(client_address || ''),
        city: String(client_city || ''),
        plan: String(plan || ''),
        machines: String(machines || 1),
        reach_in: hasReachIn ? 'true' : 'false',
      },
    };
    if (client_email) {
      customerParams.email = String(client_email);
    }
    const customer = await stripe.customers.create(customerParams);

    // --- LINE ITEMS ---
    const lineItems: Stripe.Checkout.SessionCreateParams.LineItem[] = [];

    // ENTRY FEE
    const standardEntry = 99 + extraMachines * 49;
    const entryPrice = Math.max(0, standardEntry - entryDisc);

    if (entryPrice > 0) {
      lineItems.push({
        price_data: {
          currency: 'usd',
          product_data: {
            name: 'Initial Setup Fee',
            description: 'Initial deep clean, ATP baseline, account setup',
          },
          unit_amount: Math.round(entryPrice * 100),
        },
        quantity: 1,
      });
    }

    // PLAN PRICING
    if (plan === 'onetime') {
      const basePrice  = 395 + extraMachines * 150;
      const finalPrice = Math.max(0, basePrice - planDisc);
      const machineLabel = m > 1 ? ` (${m} machines)` : '';

      lineItems.push({
        price_data: {
          currency: 'usd',
          product_data: {
            name: `One-Time Deep Clean${machineLabel}`,
            description: 'ATP testing and compliance report included',
          },
          unit_amount: Math.round(finalPrice * 100),
        },
        quantity: 1,
      });

    } else {
      const baseMonthly    = plan === 'monthly' ? 149 : 129;
      const additionalRate = plan === 'monthly' ? 69  : 49;
      const totalMonthly   = baseMonthly + extraMachines * additionalRate;
      const finalMonthly   = Math.max(0, totalMonthly - planDisc);

      const planLabel    = plan === 'monthly' ? '60-Day Clean Ice Plan' : '90-Day Clean Ice Plan';
      const visitsLabel  = plan === 'monthly' ? '6 visits/year' : '4 visits/year';
      const machineLabel = m > 1 ? ` (${m} machines)` : '';

      lineItems.push({
        price_data: {
          currency: 'usd',
          product_data: {
            name: `${planLabel}${machineLabel}`,
            description: `${visitsLabel}, ATP compliance reports, inspection protection guarantee`,
          },
          unit_amount: Math.round(finalMonthly * 100),
          recurring: { interval: 'month' },
        },
        quantity: 1,
      });

      // REACH-IN COOLER ADD-ON
      // Only for recurring plans (not one-time)
      // Uses static Stripe price IDs for the add-on subscription
      if (hasReachIn) {
        const reachInPriceId = plan === 'quarterly'
          ? STRIPE_PRICES.reach_in_quarterly
          : STRIPE_PRICES.reach_in_monthly;

        lineItems.push({
          price: reachInPriceId,
          quantity: 1,
        });
      }
    }

    // REACH-IN COOLER ADD-ON (subscription plans only)
    if (reach_in && reach_in_price_id && plan !== 'onetime') {
      lineItems.push({
        price: String(reach_in_price_id),
        quantity: 1,
      });
    }

    // --- CHECKOUT SESSION ---
    const successUrl = SUCCESS_BASE
      + '?stripe=success&pid=' + encodeURIComponent(String(prospect_id || ''));

    const termsLabel = flex
      ? 'I agree to month-to-month terms'
      : 'I agree to the 12-month service terms';

    const submitMsg = flex
      ? 'Month-to-month plan, no long-term commitment. '
        + 'Cancel anytime with 30 days written notice. '
        + 'Full terms & conditions: ' + TERMS_URL
      : '12-month service commitment. Early cancellation '
        + 'requires written notice plus a fee equal to '
        + 'two months of service. Full terms: ' + TERMS_URL;

    const sessionParams: Stripe.Checkout.SessionCreateParams = {
      mode: plan === 'onetime' ? 'payment' : 'subscription',
      customer: customer.id,
      line_items: lineItems,
      success_url: successUrl,
      cancel_url: CANCEL_URL,
      custom_fields: [
        {
          key: 'terms_agreement',
          label: { type: 'custom', custom: termsLabel },
          type: 'dropdown',
          dropdown: {
            options: [{ label: 'I agree', value: 'agreed' }],
          },
          optional: false,
        },
      ],
      custom_text: { submit: { message: submitMsg } },
      metadata: {
        prospect_id: String(prospect_id || ''),
        plan,
        machines: String(m),
        client_name: String(client_name || ''),
        flex: flex ? 'true' : 'false',
        reach_in: hasReachIn ? 'true' : 'false',
      },
      payment_method_types: ['card'],
      phone_number_collection: { enabled: true },
    };

    if (plan !== 'onetime') {
      sessionParams.subscription_data = {
        metadata: {
          prospect_id: String(prospect_id || ''),
          plan,
          machines: String(m),
          client_name: String(client_name || ''),
          flex: flex ? 'true' : 'false',
          reach_in: hasReachIn ? 'true' : 'false',
        },
      };
    }

    const session = await stripe.checkout.sessions.create(sessionParams);

    return new Response(
      JSON.stringify({ url: session.url, session_id: session.id }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    );

  } catch (error) {
    console.error('Stripe checkout error:', error);
    return new Response(
      JSON.stringify({ error: (error as Error).message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400,
      }
    );
  }
});
