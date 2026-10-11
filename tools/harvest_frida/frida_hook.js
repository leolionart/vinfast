// Hook luồng đăng ký của app VinFast: buộc cache-miss clientInstanceId để app
// tự chạy lại challenge -> Play Integrity -> client/register, và ghi lại request/response.

function log(m) { send({ t: 'log', m: String(m) }); }

Java.perform(function () {
  // 1) Ép cache-miss: giá trị UUID (clientInstanceId) trả về null.
  try {
    var ASP = Java.use('com.vinfast.companion.core.base.storage.AppSharedPreference');
    var overloads = ASP.l.overloads;
    log('AppSharedPreference.l overloads=' + overloads.length);
    overloads.forEach(function (ov) {
      log('  sig=' + ov.argumentTypes.map(function (t) { return t.className; }).join(','));
      ov.implementation = function () {
        var args = Array.prototype.slice.call(arguments);
        var v = ov.apply(this, args);
        var s = v === null ? null : String(v);
        log('prefs.l(' + args.map(String).join(' | ') + ') -> ' + (s === null ? 'null' : s.slice(0, 40)));
        if (s && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s)) {
          log('FORCE cache miss (clientInstanceId)');
          return null;
        }
        return v;
      };
    });
  } catch (e) { log('ASP hook err ' + e); }

  // 2) Ghi nonce + chữ ký
  try {
    var SC = Java.use('com.vinfast.companion.core.utils.SecureClient');
    SC.d.implementation = function (input) {
      var out = this.d(input);
      log('SecureClient.d(' + input.slice(0, 80) + ') -> ' + out);
      return out;
    };
    SC.c.implementation = function () {
      var out = this.c();
      log('SecureClient.c() -> ' + out.slice(0, 60) + '... len=' + out.length);
      return out;
    };
  } catch (e) { log('SC hook err ' + e); }

  // 3) Ghi request/response tới ccaruaa
  try {
    var TI = Java.use('com.vinfast.companion.corenetwork.interceptor.TokenInterceptor');
    TI.intercept.implementation = function (chain) {
      var req = chain.request();
      var url = req.url().toString();
      if (url.indexOf('ccaruaa') >= 0) {
        log('REQ ' + req.method() + ' ' + url);
        log('  headers: ' + req.headers().toString().replace(/\n/g, ' ; '));
        try {
          var b = req.body();
          if (b !== null) {
            var buf = Java.use('okio.Buffer').$new();
            b.writeTo(buf);
            log('  body: ' + buf.readUtf8().slice(0, 300));
          }
        } catch (x) { log('  body err ' + x); }
      }
      var resp = this.intercept(chain);
      if (url.indexOf('ccaruaa') >= 0) {
        log('RESP ' + resp.code() + ' ' + url);
        try { log('  body: ' + resp.peekBody(4096).string().slice(0, 400)); } catch (x) { log('  rb err ' + x); }
      }
      return resp;
    };
  } catch (e) { log('TI hook err ' + e); }

  log('hooks installed');
});
