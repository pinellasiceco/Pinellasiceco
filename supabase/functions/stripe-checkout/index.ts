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
      client_name,       // business name for Stripe metadata
      client_email,      // optional — pre-fills checkout email field
      prospect_id,       // for metadata/tracking and return URL
    } = await req.json();

    if (!plan || !machines || Number(machines) < 1) {
      throw new Error('Invalid parameters: plan and machines required');
    }

    const m = Math.max(1, Math.round(Number(machines)));
    const extraMachines = Math.max(0, m - 1);
    const entryDisc = Math.max(0, Math.min(Number(entry_discount) || 0, 99));
    const planDisc  = Math.max(0, Number(monthly_discount) || 0);

    const lineItems: Stripe.Checkout.SessionCreateParams.LineItem[] = [];

    // --- ENTRY FEE ---
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

    // --- PLAN PRICING ---
    if (plan === 'onetime') {
      const basePrice   = 395 + extraMachines * 150;
      const finalPrice  = Math.max(0, basePrice - planDisc);
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
      const baseMonthly     = plan === 'monthly' ? 149 : 129;
      const additionalRate  = plan === 'monthly' ? 69  : 49;
      const totalMonthly    = baseMonthly + extraMachines * additionalRate;
      const finalMonthly    = Math.max(0, totalMonthly - planDisc);

      const planLabel   = plan === 'monthly' ? '60-Day Clean Ice Plan' : '90-Day Clean Ice Plan';
      const visitsLabel = plan === 'monthly' ? '6 visits/year' : '4 visits/year';
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
    }

    // --- CHECKOUT SESSION ---
    const successUrl = SUCCESS_BASE
      + '?stripe=success&pid=' + encodeURIComponent(String(prospect_id || ''));

    const sessionParams: Stripe.Checkout.SessionCreateParams = {
      mode: plan === 'onetime' ? 'payment' : 'subscription',
      line_items: lineItems,
      success_url: successUrl,
      cancel_url: CANCEL_URL,
      customer_creation: 'always',
      custom_fields: [
        {
          key: 'terms_agreement',
          label: {
            type: 'custom',
            custom:
              'I agree to the 12-month service term and Terms & Conditions '
              + '(pinellasiceco.com/terms). Early cancellation requires '
              + 'written notice and a fee equal to two months of service.',
          },
          type: 'dropdown',
          dropdown: {
            options: [{ label: 'I agree', value: 'agreed' }],
          },
          optional: false,
        },
      ],
      custom_text: {
        submit: {
          message:
            'By completing payment you agree to the Pinellas Ice Co '
            + `Terms & Conditions at ${TERMS_URL}`,
        },
      },
      metadata: {
        prospect_id: String(prospect_id || ''),
        plan,
        machines: String(m),
        client_name: String(client_name || ''),
      },
      payment_method_types: ['card'],
      phone_number_collection: { enabled: true },
    };

    if (client_email) {
      sessionParams.customer_email = String(client_email);
    }

    if (plan !== 'onetime') {
      sessionParams.subscription_data = {
        metadata: {
          prospect_id: String(prospect_id || ''),
          plan,
          machines: String(m),
          client_name: String(client_name || ''),
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
