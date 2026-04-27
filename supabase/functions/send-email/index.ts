import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: cors })
  }
  try {
    const { to, subject, html } = await req.json()
    const apiKey = Deno.env.get('RESEND_API_KEY') ?? ''
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'RESEND_API_KEY not set' }), {
        headers: { ...cors, 'Content-Type': 'application/json' }, status: 500,
      })
    }
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: 'service@pinellasiceco.com',
        to: Array.isArray(to) ? to : [to],
        subject,
        html,
      }),
    })
    const data = await res.json()
    return new Response(JSON.stringify(data), {
      headers: { ...cors, 'Content-Type': 'application/json' },
      status: res.ok ? 200 : 400,
    })
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      headers: { ...cors, 'Content-Type': 'application/json' }, status: 500,
    })
  }
})
