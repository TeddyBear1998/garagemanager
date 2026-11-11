// "Watch" buttons: <button type="button" data-watch="achievebear-goal">…</button> opens that video in a
// player over the page; nothing plays or loads until it's asked for. Wide screens get the 16:9
// version (/video/<id>-<lang>-wide.mp4), phones and narrow windows the tall one (<id>-<lang>.mp4).
// The page's language comes from <html lang>. Escape, the × button or a click outside closes it.
// The same file is used by every IBS site.
(function () {
  var CSS =
    '.watch-dialog{padding:0;border:0;background:transparent;max-width:none;max-height:none;overflow:visible}' +
    '.watch-dialog::backdrop{background:rgba(17,14,11,.86)}' +
    '.watch-dialog video{display:block;width:min(92vw,calc(84vh*16/9),1280px);height:auto;aspect-ratio:16/9;' +
    'border-radius:12px;background:#110e0b;box-shadow:0 20px 60px rgba(0,0,0,.5)}' +
    '.watch-dialog.tall video{width:min(92vw,calc(84vh*9/16),440px);aspect-ratio:9/16}' +
    '.watch-close{position:absolute;top:-46px;right:0;width:38px;height:38px;border-radius:50%;border:0;' +
    'background:rgba(255,255,255,.16);color:#fff;font:600 24px/38px system-ui,sans-serif;cursor:pointer;padding:0}' +
    '.watch-close:hover{background:rgba(255,255,255,.28)}' +
    '.watch-close:focus-visible{outline:2px solid #fff;outline-offset:2px}'
  var dialog, video

  function lang() { return document.documentElement.lang === 'lv' ? 'lv' : 'en' }
  function wide() { return window.matchMedia('(min-width: 760px) and (min-aspect-ratio: 1/1)').matches }

  function build() {
    var style = document.createElement('style')
    style.textContent = CSS
    document.head.appendChild(style)
    dialog = document.createElement('dialog')
    dialog.className = 'watch-dialog'
    var close = document.createElement('button')
    close.type = 'button'
    close.className = 'watch-close'
    close.textContent = '×'
    close.setAttribute('aria-label', lang() === 'lv' ? 'Aizvērt' : 'Close')
    close.addEventListener('click', function () { dialog.close() })
    video = document.createElement('video')
    video.controls = true
    video.playsInline = true
    dialog.appendChild(close)
    dialog.appendChild(video)
    // A click on the dark area around the video lands on the dialog itself.
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close() })
    dialog.addEventListener('close', function () {
      video.pause()
      video.removeAttribute('src')
      video.load()
    })
    document.body.appendChild(dialog)
  }

  function open(id, label) {
    if (!dialog) build()
    var w = wide()
    var base = '/video/' + id + '-' + lang() + (w ? '-wide' : '')
    dialog.classList.toggle('tall', !w)
    dialog.setAttribute('aria-label', label)
    video.poster = base + '.jpg'
    video.src = base + '.mp4'
    dialog.showModal()
    var played = video.play()
    if (played && played.catch) played.catch(function () {})   // the controls are there if autoplay is refused
  }

  document.addEventListener('click', function (e) {
    var button = e.target.closest && e.target.closest('[data-watch]')
    if (!button || typeof HTMLDialogElement !== 'function') return
    e.preventDefault()
    open(button.getAttribute('data-watch'), button.textContent.trim())
  })
})()
