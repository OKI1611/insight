# -*- coding: utf-8 -*-
"""후원 페이지(support.html)의 「해외에서 후원하기」 영역을 5개 언어로 만들어 끼운다.

사용: python tools/support_overseas.py
  - support.html 의 <!-- OVERSEAS:START --> ~ <!-- OVERSEAS:END --> 사이를 통째로 다시 쓴다.
  - 문구를 고칠 때는 이 파일의 T 사전을 고친 뒤 다시 실행한다.
  - PayPal 사실 확인(2026-11-26, PayPal 고객센터): PayPal.me 로 보내려면 PayPal 계정 필요 · 보낸 뒤 취소 불가 ·
    수수료와 환율은 보내는 나라·수단에 따라 다름(paypal.com/fees). 확인되지 않은 약속은 쓰지 않는다.
"""
import os, re, sys
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['ko', 'en', 'es', 'ja', 'zh']

T = {
 'ko': dict(
  eyebrow='GIVE FROM ABROAD',
  h='해외에서 후원하기',
  intro='한국 밖에 계신 분은 아래 두 가지 방법으로 후원하실 수 있습니다. 토스·카카오페이·국내 계좌이체는 해외에서 쓰기 어렵습니다.',
  m1='방법 1 · PayPal (가장 간편)',
  steps=[
   '아래 <b>「PayPal로 후원하기」</b> 단추를 누르면 PayPal 후원 페이지(<b>paypal.me/oki1611</b>)가 열립니다.',
   'PayPal 계정으로 로그인합니다. PayPal.me로 보내려면 <b>PayPal 계정이 필요</b>합니다. 계정이 없으면 paypal.com에서 무료로 만들 수 있습니다.',
   '후원할 <b>금액</b>을 입력합니다. 통화를 고를 수 있으면 편한 통화(USD 등)를 고르세요.',
   '메모(note)에 <b>이름이나 이메일</b>을 남겨 주시면 감사 인사를 드리겠습니다(선택).',
   'PayPal이 결제 유형을 물으면, 이 후원에는 <b>물품이나 서비스가 제공되지 않는다</b>는 점을 참고해 골라 주세요.',
   '금액과 받는 곳(oki1611)을 확인하고 <b>보내기</b>를 누릅니다. <b>보낸 뒤에는 취소할 수 없으니</b> 금액을 꼭 확인해 주세요.'],
  btn='PayPal로 후원하기',
  fee='PayPal 수수료와 환율은 보내는 나라와 결제 수단에 따라 다릅니다. 자세한 내용은 <a href="https://www.paypal.com/fees" target="_blank" rel="noopener" class="underline">PayPal 수수료 안내</a>에서 확인해 주세요.',
  m2='방법 2 · 국제 송금 (은행 해외송금)',
  m2intro='거래 은행의 창구나 인터넷뱅킹 해외송금 메뉴에서 아래 정보를 그대로 입력해 주세요.',
  wire=[
   '받는 사람 이름은 영문 <b>OH KWANG IL</b> 그대로 적어 주세요.',
   '보내는 은행과 중계은행(intermediary bank) 수수료가 붙어 실제 도착 금액이 줄어들 수 있습니다.',
   '송금 메모(참조)에 <b>BIBLY</b>와 보내는 분 이름을 적어 주시면 확인이 쉽습니다.'],
  common='후원은 전적으로 자발적이며 어떤 대가도 따르지 않습니다. 기부금 영수증(세금 공제용)은 한국과 해외 모두 발행되지 않습니다. 후원 확인이나 문의는 <a href="mailto:contact@biblynote.com" class="underline">contact@biblynote.com</a>으로 보내 주세요.',
  copy='복사', copied='복사했어요'),
 'en': dict(
  eyebrow='GIVE FROM ABROAD',
  h='Give from outside Korea',
  intro='If you live outside Korea, you can support this ministry in two ways. Toss, KakaoPay and Korean bank transfers are hard to use from abroad.',
  m1='Option 1 · PayPal (easiest)',
  steps=[
   'Tap <b>“Give with PayPal”</b> below. Our PayPal page (<b>paypal.me/oki1611</b>) will open.',
   'Log in to PayPal. Sending through PayPal.me <b>requires a PayPal account</b>. If you don’t have one, you can open one free at paypal.com.',
   'Enter the <b>amount</b> you wish to give. If PayPal lets you choose a currency, pick the one that suits you (for example, USD).',
   'In the note, you may add <b>your name or email</b> so we can thank you (optional).',
   'If PayPal asks you to choose a payment type, please keep in mind that <b>no goods or services are provided</b> in return for this gift.',
   'Check the amount and the recipient (oki1611), then tap <b>Send</b>. <b>A payment cannot be cancelled once it is sent</b>, so please double-check the amount.'],
  btn='Give with PayPal',
  fee='PayPal fees and exchange rates depend on your country and payment method. Please see <a href="https://www.paypal.com/fees" target="_blank" rel="noopener" class="underline">PayPal’s fee page</a> for details.',
  m2='Option 2 · International bank transfer (wire)',
  m2intro='At your bank, or in your online banking’s international transfer menu, enter the details below exactly as shown.',
  wire=[
   'Enter the recipient name exactly as <b>OH KWANG IL</b>.',
   'Your bank and any intermediary bank may charge fees, so the amount that arrives may be smaller.',
   'Adding <b>BIBLY</b> and your name to the transfer reference helps us confirm your gift.'],
  common='All gifts are entirely voluntary and nothing is given in return. We are not able to issue tax-deductible donation receipts in Korea or in any other country. To confirm a gift or ask a question, please write to <a href="mailto:contact@biblynote.com" class="underline">contact@biblynote.com</a>.',
  copy='Copy', copied='Copied'),
 'es': dict(
  eyebrow='DONAR DESDE EL EXTRANJERO',
  h='Donar desde fuera de Corea',
  intro='Si usted vive fuera de Corea, puede apoyar este ministerio de dos maneras. Toss, KakaoPay y las transferencias bancarias coreanas son difíciles de usar desde el extranjero.',
  m1='Opción 1 · PayPal (la más sencilla)',
  steps=[
   'Pulse <b>«Donar con PayPal»</b> abajo. Se abrirá nuestra página de PayPal (<b>paypal.me/oki1611</b>).',
   'Inicie sesión en PayPal. Para enviar por PayPal.me <b>se necesita una cuenta de PayPal</b>. Si no la tiene, puede abrir una gratis en paypal.com.',
   'Escriba el <b>monto</b> que desea donar. Si PayPal le permite elegir la moneda, elija la que le resulte cómoda (por ejemplo, USD).',
   'En la nota puede escribir <b>su nombre o correo</b> para que podamos darle las gracias (opcional).',
   'Si PayPal le pide elegir un tipo de pago, tenga en cuenta que <b>esta donación no incluye ningún producto ni servicio</b> a cambio.',
   'Revise el monto y el destinatario (oki1611) y pulse <b>Enviar</b>. <b>Un pago enviado no se puede cancelar</b>, así que verifique bien el monto.'],
  btn='Donar con PayPal',
  fee='Las comisiones y el tipo de cambio de PayPal dependen de su país y del medio de pago. Consulte los detalles en la <a href="https://www.paypal.com/fees" target="_blank" rel="noopener" class="underline">página de comisiones de PayPal</a>.',
  m2='Opción 2 · Transferencia bancaria internacional',
  m2intro='En su banco, o en la sección de transferencias internacionales de su banca en línea, escriba los datos de abajo tal como aparecen.',
  wire=[
   'Escriba el nombre del beneficiario exactamente como <b>OH KWANG IL</b>.',
   'Su banco y el banco intermediario pueden cobrar comisiones, por lo que el monto que llegue puede ser menor.',
   'Si añade <b>BIBLY</b> y su nombre en la referencia de la transferencia, nos será más fácil confirmar su donación.'],
  common='Toda donación es completamente voluntaria y no conlleva ninguna contraprestación. No podemos emitir recibos de donación deducibles de impuestos, ni en Corea ni en otros países. Para confirmar una donación o hacer una consulta, escriba a <a href="mailto:contact@biblynote.com" class="underline">contact@biblynote.com</a>.',
  copy='Copiar', copied='Copiado'),
 'ja': dict(
  eyebrow='GIVE FROM ABROAD',
  h='海外からのご支援',
  intro='韓国国外にお住まいの方は、次の二つの方法でご支援いただけます。Toss・カカオペイ・韓国国内の口座振込は、海外からはご利用が難しいためです。',
  m1='方法1 ・ PayPal(いちばん簡単です)',
  steps=[
   '下の<b>「PayPalで支援する」</b>ボタンを押すと、PayPalの支援ページ(<b>paypal.me/oki1611</b>)が開きます。',
   'PayPalにログインします。PayPal.meで送金するには<b>PayPalアカウントが必要</b>です。お持ちでない方は paypal.com で無料で作成できます。',
   'ご支援の<b>金額</b>を入力します。通貨を選べる場合は、使いやすい通貨(USDなど)をお選びください。',
   'メモ(note)に<b>お名前やメールアドレス</b>を書いていただければ、お礼をお送りします(任意)。',
   'PayPalから支払いの種類を尋ねられた場合は、このご支援には<b>商品やサービスの提供がない</b>ことをふまえてお選びください。',
   '金額と送金先(oki1611)を確認し、<b>送金</b>を押します。<b>送金後は取り消しができません</b>ので、金額を必ずご確認ください。'],
  btn='PayPalで支援する',
  fee='PayPalの手数料と為替レートは、お住まいの国と支払い方法によって異なります。詳しくは<a href="https://www.paypal.com/fees" target="_blank" rel="noopener" class="underline">PayPalの手数料のご案内</a>をご確認ください。',
  m2='方法2 ・ 海外送金(銀行の国際送金)',
  m2intro='お取引銀行の窓口、またはインターネットバンキングの海外送金メニューで、下の情報をそのままご入力ください。',
  wire=[
   '受取人名は英字で <b>OH KWANG IL</b> とそのままご記入ください。',
   '送金銀行や中継銀行(intermediary bank)の手数料がかかり、実際に届く金額が少なくなる場合があります。',
   '送金メッセージ(参照欄)に <b>BIBLY</b> とお名前を書いていただくと、確認がしやすくなります。'],
  common='ご支援はまったくの任意であり、見返りは一切ありません。寄付金控除のための領収書は、韓国でも海外でも発行しておりません。ご支援の確認やお問い合わせは <a href="mailto:contact@biblynote.com" class="underline">contact@biblynote.com</a> までお送りください。',
  copy='コピー', copied='コピーしました'),
 'zh': dict(
  eyebrow='GIVE FROM ABROAD',
  h='從海外奉獻支持',
  intro='住在韓國以外的朋友，可以透過下面兩種方式支持這個事工。Toss、KakaoPay 和韓國國內轉帳，在海外不容易使用。',
  m1='方式一・PayPal（最簡便）',
  steps=[
   '按下方的<b>「用 PayPal 奉獻」</b>，就會開啟我們的 PayPal 頁面（<b>paypal.me/oki1611</b>）。',
   '登入 PayPal。透過 PayPal.me 付款<b>需要有 PayPal 帳戶</b>。如果還沒有帳戶，可以在 paypal.com 免費申請。',
   '輸入奉獻<b>金額</b>。如果可以選擇幣別，請選您方便的幣別（例如 USD）。',
   '可以在附註（note）留下<b>您的姓名或電子郵件</b>，方便我們向您致謝（自由填寫）。',
   '如果 PayPal 請您選擇付款類型，請留意：這筆奉獻<b>不會換取任何商品或服務</b>。',
   '確認金額和收款對象（oki1611）後，按下<b>付款</b>。<b>付款送出後就無法取消</b>，請務必再次確認金額。'],
  btn='用 PayPal 奉獻',
  fee='PayPal 的手續費和匯率，會依您所在的國家和付款方式而不同。詳情請參考 <a href="https://www.paypal.com/fees" target="_blank" rel="noopener" class="underline">PayPal 手續費說明</a>。',
  m2='方式二・國際匯款（銀行電匯）',
  m2intro='請在您往來銀行的櫃台，或網路銀行的國際匯款功能中，照下面的資料輸入。',
  wire=[
   '收款人姓名請照英文 <b>OH KWANG IL</b> 填寫。',
   '匯出銀行和中轉銀行（intermediary bank）可能收取手續費，實際到帳金額可能會減少。',
   '若在匯款附言中寫上 <b>BIBLY</b> 和您的姓名，我們會比較容易確認。'],
  common='所有奉獻都完全出於自願，不會有任何回報。我們無法開立可抵稅的奉獻收據（韓國及其他國家皆然）。如需確認奉獻或有任何問題，請寫信到 <a href="mailto:contact@biblynote.com" class="underline">contact@biblynote.com</a>。',
  copy='複製', copied='已複製'),
}

def block(L, html_):
    return f'<div data-l="{L}" lang="{ {"zh":"zh-Hant"}.get(L, L) }">{html_}</div>'

def build():
    o = []
    o.append('<!-- OVERSEAS:START — tools/support_overseas.py 가 만든다. 직접 고치지 말 것 -->')
    o.append('<section id="overseas" class="ovs max-w-md mx-auto mb-8 text-left bg-white rounded-3xl border-2 border-[#0070ba]/30 shadow-[0_18px_50px_-22px_rgba(0,48,135,.35)] p-6 scroll-mt-24">')
    head = ''.join(block(L, f'<p class="text-[#0070ba] text-xs font-bold tracking-[0.18em] uppercase mb-1">{T[L]["eyebrow"]}</p>'
                            f'<h2 class="text-xl font-bold text-neutral-900 mb-2">{T[L]["h"]}</h2>'
                            f'<p class="text-neutral-600 text-[15px] leading-relaxed mb-5">{T[L]["intro"]}</p>'
                            f'<h3 class="font-bold text-neutral-900 text-base mb-2.5">{T[L]["m1"]}</h3>'
                            '<ol class="ovs-steps">' + ''.join(f'<li>{s}</li>' for s in T[L]['steps']) + '</ol>') for L in LANGS)
    o.append(head)
    o.append('<a id="paypalGive" href="https://paypal.me/oki1611" target="_blank" rel="noopener" class="mt-4 flex items-center justify-center gap-2 bg-[#0070ba] text-white font-bold text-[16px] min-h-[52px] rounded-2xl hover:opacity-90 transition">'
             '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7.1 21.3H3.6a.6.6 0 0 1-.6-.7L5.7 3.4A.9.9 0 0 1 6.6 2.7h6.6c3.5 0 5.6 1.8 5 5.1-.6 3.9-3.2 5.6-6.6 5.6H9.4l-1.3 7.3a.6.6 0 0 1-.6.6zm2.9-9.6h1.5c2 0 3.3-.9 3.6-2.9.3-1.7-.7-2.5-2.5-2.5h-1.4z"/></svg>'
             + ''.join(f'<span data-l="{L}">{T[L]["btn"]}</span>' for L in LANGS) + '</a>')
    o.append(''.join(block(L, f'<p class="text-neutral-500 text-xs leading-relaxed mt-3">{T[L]["fee"]}</p>') for L in LANGS))
    # 국제 송금 — site.json support.foreign 이 채워졌을 때만 보인다(support.html 스크립트가 #foreignBox 를 켠다)
    o.append('<div id="foreignBox" style="display:none" class="mt-7 pt-6 border-t border-neutral-200">')
    o.append(''.join(block(L, f'<h3 class="font-bold text-neutral-900 text-base mb-1.5">{T[L]["m2"]}</h3>'
                              f'<p class="text-neutral-600 text-sm leading-relaxed mb-3.5">{T[L]["m2intro"]}</p>') for L in LANGS))
    cp = ''.join(f'<span data-l="{L}">{T[L]["copy"]}</span>' for L in LANGS)
    def row(label, vid, copy=False, extra=''):
        btn = f'<button type="button" onclick="copyVal(\'{vid}\')" class="ovs-copy">{cp}</button>' if copy else ''
        return (f'<div class="flex items-center justify-between gap-3 py-2 border-b border-neutral-100"{extra}>'
                f'<span class="text-neutral-400 text-xs shrink-0">{label}</span>'
                f'<span class="flex items-center gap-2 text-right"><span id="{vid}" class="font-semibold text-neutral-900 text-sm break-all"></span>{btn}</span></div>')
    o.append('<div class="bg-sand/40 rounded-2xl px-4 py-1.5">'
             + row('Bank', 'fBank') + row('SWIFT / BIC', 'fSwift', True) + row('Account No.', 'fAcct', True)
             + row('Account holder', 'fHolder', True) + row('Currency', 'fCur', False, ' id="fCurRow"')
             + row('Bank address', 'fAddr', False, ' id="fAddrRow"') + '</div>')
    o.append(''.join(block(L, '<ul class="ovs-notes">' + ''.join(f'<li>{s}</li>' for s in T[L]['wire']) + '</ul>') for L in LANGS))
    o.append('</div>')
    o.append(''.join(block(L, f'<p class="text-neutral-500 text-xs leading-relaxed mt-6 pt-4 border-t border-neutral-100">{T[L]["common"]}</p>') for L in LANGS))
    o.append('</section>')
    o.append('<script>window.__OVS_COPIED = ' + repr({L: T[L]['copied'] for L in LANGS}).replace("'", '"') + ';</script>')
    o.append('<!-- OVERSEAS:END -->')
    return '\n        '.join(o)

def main():
    p = f'{ROOT}/support.html'
    s = open(p, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    new = build()
    if crlf: new = new.replace('\n', '\r\n')
    s2, n = re.subn(r'<!-- OVERSEAS:START.*?<!-- OVERSEAS:END -->', lambda m: new, s, flags=re.S)
    if n != 1: raise SystemExit('support.html 에 OVERSEAS 표시가 없습니다')
    open(p, 'w', encoding='utf-8', newline='').write(s2)
    print('support.html 해외 후원 영역 갱신 (5개 언어)')

if __name__ == '__main__':
    main()
