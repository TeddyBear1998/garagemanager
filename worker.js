// Runs only for /video/* (run_worker_first in wrangler.jsonc); everything else is served as a
// plain static file. Cloudflare's static files answer a Range request with the whole file, and
// Safari won't play a <video> unless it gets the part it asked for (206), so this cuts it out.
// The same file is used by every IBS site.
export default {
  async fetch(request, env) {
    const range = request.headers.get('range')
    // Ask for the whole file; the static file server ignores Range anyway.
    const headers = new Headers(request.headers)
    headers.delete('range')
    const res = await env.ASSETS.fetch(new Request(request, { headers }))
    if (res.status !== 200) return res
    const out = new Headers(res.headers)
    out.set('accept-ranges', 'bytes')          // tells the browser it may ask for parts
    if (!range || request.method !== 'GET') return new Response(res.body, { status: 200, headers: out })

    const body = await res.arrayBuffer()
    const size = body.byteLength
    const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim())
    let start, end
    if (m && m[1] !== '') {
      start = +m[1]
      end = m[2] === '' ? size - 1 : Math.min(+m[2], size - 1)
    } else if (m && m[2] !== '') {
      start = Math.max(size - +m[2], 0)     // bytes=-500: the last 500 bytes
      end = size - 1
    }
    if (start === undefined || start > end || start >= size) {
      out.set('content-range', `bytes */${size}`)
      out.delete('content-length')
      return new Response(null, { status: 416, headers: out })
    }
    out.set('content-range', `bytes ${start}-${end}/${size}`)
    out.set('content-length', String(end - start + 1))
    return new Response(body.slice(start, end + 1), { status: 206, headers: out })
  },
}
