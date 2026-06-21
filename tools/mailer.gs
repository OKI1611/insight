// ============================================================
// BIBLY 메일러 — Google Apps Script 웹앱 (고객 자동 확인메일 발송용)
// ------------------------------------------------------------
// [배포 방법]
// 1) https://script.google.com 접속 → '새 프로젝트'
// 2) 이 코드 전체를 붙여넣고 저장
// 3) 우측 상단 '배포' → '새 배포' → 유형: '웹 앱'
//    - 설명: BIBLY mailer
//    - 실행 계정: '나'
//    - 액세스 권한: '모든 사용자'
//    → '배포' 클릭 → 권한 승인(본인 Gmail로 발송 허용)
// 4) 표시되는 '웹 앱 URL'(https://script.google.com/macros/s/.../exec) 복사
// 5) content/site.json 의 support.mailer_url 에 그 URL을 붙여넣고 저장·배포
//    → 이제 관리자 페이지에서 이용권/교재를 '부여'하면 고객에게 자동 발송됨.
// ------------------------------------------------------------
// ※ 무료 Gmail은 하루 약 100통, Google Workspace는 약 1,500통 발송 한도.
// ※ TOKEN 은 admin.html 의 토큰과 같아야 함(기본 'BIBLY-MAILER').
// ============================================================

var TOKEN = 'BIBLY-MAILER';

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    if (d.token !== TOKEN) return ContentService.createTextOutput('bad-token');
    if (!d.to) return ContentService.createTextOutput('no-to');
    MailApp.sendEmail({
      to: d.to,
      subject: d.subject || 'BIBLY 안내',
      htmlBody: d.html || '',
      name: 'BIBLY 바이블 인사이트'
    });
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('err:' + err);
  }
}

function doGet() {
  return ContentService.createTextOutput('BIBLY mailer ready');
}
