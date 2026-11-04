/* Google AdSense. Ads stay off until ADSENSE_CLIENT is filled in.
   1. AdSense → Account → your publisher ID, e.g. "ca-pub-1234567890123456"
   2. AdSense → Ads → By ad unit → Display ads → create one responsive unit and paste
      its "data-ad-slot" number below (it serves both spots).
   3. AdSense → Privacy & messaging → turn on the European regulations (GDPR) message.
      That is Google's own certified consent banner; it appears automatically.
   The page marks where an ad may go with <div class="ad" data-ad="page">: one after the
   features, one at the bottom. Never next to the download buttons.
   data-size="320x50" gives a spot a fixed size instead of a responsive one.
   Spots are filled once, never redrawn. The GearBear app itself never shows ads. */
'use strict'
;(function () {
  var ADSENSE_CLIENT = ''              // fill in after approval: 'ca-pub-6187091179864351'
  // Ad unit IDs, e.g. '1234567890'. One ID may be reused for several spots.
  var SLOTS = {
    page: '',     // both spots on the website (responsive display unit)
  }

  // Spots for another screen size (data-media) are skipped, not loaded hidden.
  var spots = Array.prototype.filter.call(document.querySelectorAll('.ad[data-ad]'), function (el) {
    return !el.dataset.media || window.matchMedia(el.dataset.media).matches
  })
  if (!ADSENSE_CLIENT || !spots.length || !navigator.onLine) return

  var s = document.createElement('script')
  s.async = true
  s.crossOrigin = 'anonymous'
  s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(ADSENSE_CLIENT)
  document.head.appendChild(s)

  var lv = document.documentElement.lang === 'lv'
  spots.forEach(function (spot) {
    var slot = SLOTS[spot.dataset.ad]
    if (!slot) return
    spot.innerHTML = '<span class="ad-label">' + (lv ? 'Reklāma' : 'Advertisement') + '</span>'
    var ins = document.createElement('ins')
    ins.className = 'adsbygoogle'
    ins.style.display = 'block'
    ins.setAttribute('data-ad-client', ADSENSE_CLIENT)
    ins.setAttribute('data-ad-slot', slot)
    var size = /^(\d+)x(\d+)$/.exec(spot.dataset.size || '')
    if (size) {
      ins.style.display = 'inline-block'
      ins.style.width = size[1] + 'px'
      ins.style.height = size[2] + 'px'
    } else {
      ins.setAttribute('data-ad-format', 'auto')
      ins.setAttribute('data-full-width-responsive', 'true')
    }
    spot.appendChild(ins)
    spot.hidden = false
    ;(window.adsbygoogle = window.adsbygoogle || []).push({})
  })
})()
