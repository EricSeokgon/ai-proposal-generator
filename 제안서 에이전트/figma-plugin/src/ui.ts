// ═══════════════════════════════════════════════════════
// UI Thread v5: JSON 입력 (Puppeteer 렌더링 결과)
// CSS 파싱 불필요 — 브라우저가 이미 모든 계산을 완료
// ═══════════════════════════════════════════════════════

var dropZone = document.getElementById('dropZone')!;
var fileInput = document.getElementById('fileInput') as HTMLInputElement;
var convertBtn = document.getElementById('convertBtn') as HTMLButtonElement;
var statusEl = document.getElementById('status')!;
var progressWrap = document.getElementById('progressWrap')!;
var progressFill = document.getElementById('progressFill')!;
var progressText = document.getElementById('progressText')!;
var loadedData: any = null;

dropZone.addEventListener('click', function() { fileInput.click(); });
dropZone.addEventListener('dragover', function(e) { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', function() { dropZone.classList.remove('dragover'); });
dropZone.addEventListener('drop', function(e) {
  e.preventDefault(); dropZone.classList.remove('dragover');
  if (e.dataTransfer?.files[0]) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', function() { if (fileInput.files?.[0]) handleFile(fileInput.files[0]); });

function handleFile(file: File) {
  if (!file.name.endsWith('.json')) {
    setStatus('.figma.json 파일만 지원합니다', 'error');
    return;
  }
  var reader = new FileReader();
  reader.onload = function(e) {
    try {
      loadedData = JSON.parse(e.target?.result as string);
      if (!Array.isArray(loadedData) || loadedData.length === 0) {
        setStatus('유효하지 않은 JSON 형식', 'error');
        return;
      }
      setStatus(file.name + ' — ' + loadedData.length + '개 슬라이드', 'success');
      convertBtn.disabled = false;
      dropZone.querySelector('p')!.textContent = file.name;
    } catch (err: any) {
      setStatus('JSON 파싱 오류: ' + err.message, 'error');
    }
  };
  reader.readAsText(file);
}

convertBtn.addEventListener('click', function() {
  if (!loadedData) return;
  convertBtn.disabled = true;
  progressWrap.style.display = 'block';
  setProgress(10, 'Figma 변환 중...');

  parent.postMessage({
    pluginMessage: { type: 'CREATE_SLIDES', slides: loadedData, totalSlides: loadedData.length }
  }, '*');
});

window.onmessage = function(event) {
  var msg = event.data.pluginMessage; if (!msg) return;
  if (msg.type === 'PROGRESS') setProgress(msg.percent, msg.message);
  else if (msg.type === 'COMPLETE') {
    setProgress(100, '완료!');
    setStatus(msg.slideCount + '개 슬라이드 변환 완료!', 'success');
    convertBtn.disabled = false;
  } else if (msg.type === 'ERROR') {
    setStatus('오류: ' + msg.message, 'error');
    convertBtn.disabled = false;
  }
};

function setStatus(m: string, t: string) { statusEl.textContent = m; statusEl.className = 'status ' + t; }
function setProgress(p: number, m: string) { progressFill.style.width = p + '%'; progressText.textContent = m; }
