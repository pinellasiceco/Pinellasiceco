import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

const GITHUB_PAT = Deno.env.get('GITHUB_PAT') ?? ''
const REPO_OWNER = 'pinellasiceco'
const REPO_NAME = 'Pinellasiceco'
const WORKFLOW_FILE = 'rebuild.yml'

serve(async (_req) => {
  try {
    const response = await fetch(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${GITHUB_PAT}`,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    )

    if (response.status === 204) {
      console.log('Rebuild triggered successfully')
      return new Response(
        JSON.stringify({ success: true }),
        { headers: { 'Content-Type': 'application/json' } }
      )
    } else {
      const body = await response.text()
      console.error(`GitHub API error: ${response.status} ${body}`)
      return new Response(
        JSON.stringify({ success: false, error: body }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }
  } catch (err) {
    console.error('Trigger failed:', err)
    return new Response(
      JSON.stringify({ success: false, error: String(err) }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
