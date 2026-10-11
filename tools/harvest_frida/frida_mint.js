// Chạy TRONG tiến trình com.vinfast.companion.app.
// Sinh Play Integrity token cho nonce tuỳ ý; kết quả trả qua send(), KHÔNG qua promise RPC.

function log(m) { send({ t: 'log', m: String(m) }); }

rpc.exports = {
  deviceid: function () {
    var out = null;
    Java.perform(function () {
      var ActivityThread = Java.use('android.app.ActivityThread');
      var app = ActivityThread.currentApplication();
      var ctx = app.getApplicationContext();
      var Secure = Java.use('android.provider.Settings$Secure');
      out = Secure.getString(ctx.getContentResolver(), 'android_id');
    });
    return out;
  },

  // Bắt đầu xin token; trả về ngay. Kết quả đến qua send({t:'token'|'error'}).
  mint: function (nonce) {
    Java.perform(function () {
      try {
        var ActivityThread = Java.use('android.app.ActivityThread');
        var app = ActivityThread.currentApplication();
        var ctx = app.getApplicationContext();
        var IMF = Java.use('com.google.android.play.core.integrity.IntegrityManagerFactory');
        var ITR = Java.use('com.google.android.play.core.integrity.IntegrityTokenRequest');
        var mgr = IMF.create(ctx);
        var builder = ITR.builder();
        builder.setNonce(nonce);
        var task = mgr.requestIntegrityToken(builder.build());
        log('request sent');

        var OnSuccessListener = Java.use('com.google.android.gms.tasks.OnSuccessListener');
        var OnFailureListener = Java.use('com.google.android.gms.tasks.OnFailureListener');

        var succ = Java.registerClass({
          name: 'vf.Succ' + Math.floor(Math.random() * 1e9),
          implements: [OnSuccessListener],
          methods: {
            onSuccess: function (obj) {
              try {
                log('obj class=' + obj.getClass().getName());
                var Resp = Java.use('com.google.android.play.core.integrity.IntegrityTokenResponse');
                var r = Java.cast(obj, Resp);
                var t = String(r.token());
                log('token len=' + t.length);
                send({ t: 'token', v: t });
              } catch (e) {
                send({ t: 'error', v: 'token err: ' + e });
              }
            }
          }
        });

        var fail = Java.registerClass({
          name: 'vf.Fail' + Math.floor(Math.random() * 1e9),
          implements: [OnFailureListener],
          methods: {
            onFailure: function (e) {
              var msg;
              try { msg = e.getClass().getName() + ': ' + e.getMessage(); }
              catch (x) { msg = String(e); }
              send({ t: 'error', v: msg });
            }
          }
        });

        task.addOnSuccessListener(succ.$new());
        task.addOnFailureListener(fail.$new());
      } catch (e) {
        var m;
        try { m = e.getClass().getName() + ': ' + e.getMessage(); } catch (x) { m = String(e); }
        send({ t: 'error', v: m });
      }
    });
    return true;
  }
};
