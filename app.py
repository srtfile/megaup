import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

API = "https://enc-dec.app/api"

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MegaUp Extractor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; padding: 20px; }
  .container { max-width: 900px; margin: 0 auto; }
  h1 { text-align: center; color: #4caf50; margin-bottom: 8px; font-size: 2rem; }
  .subtitle { text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9rem; }
  .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  label { display: block; margin-bottom: 6px; color: #aaa; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
  input { width: 100%; padding: 10px 14px; background: #0f0f1a; border: 1px solid #3a3a5a; border-radius: 8px; color: #e0e0e0; font-size: 0.95rem; margin-bottom: 16px; outline: none; }
  input:focus { border-color: #4caf50; }
  button { width: 100%; padding: 12px; background: #4caf50; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
  button:hover { background: #388e3c; }
  button:disabled { background: #444; cursor: not-allowed; }
  .output { background: #0a0a15; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; min-height: 120px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all; color: #a0f0a0; }
  .step { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #2a2a4a; color: #888; font-size: 0.85rem; }
  .step:last-child { border-bottom: none; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #444; flex-shrink: 0; }
  .step.done .dot { background: #4caf50; }
  .step.active .dot { background: #4caf50; animation: pulse 1s infinite; }
  .step.error .dot { background: #f44336; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; background: #2a2a4a; color: #4caf50; margin-left: 8px; }
  .error-msg { color: #f44336; }
  .hint { font-size: 0.78rem; color: #666; margin-top: -10px; margin-bottom: 12px; }
</style>
</head>
<body>
<div class="container">
  <h1>⬆ MegaUp</h1>
  <p class="subtitle">Decrypt AnimeKai embed URLs via MegaUp player</p>
  <div class="card">
    <label>AnimeKai Links/View URL</label>
    <input type="text" id="url" value="https://animekai.to/ajax/links/view?id=dIG98qei6A&_=xQm9tJfLwGhz_0Eq8S_YAHYkwp-qSvLfm50W5X1nyd2NnAcpzTUWyAgck4I" placeholder="https://animekai.to/ajax/links/view?id=...">
    <p class="hint">Any URL returned by AnimeKai (any domain supported)</p>
    <button id="runBtn" onclick="run()">▶ Extract Stream Data</button>
  </div>
  <div class="card">
    <label>Progress</label>
    <div id="steps">
      <div class="step" id="s1"><div class="dot"></div> Fetch & Decrypt Embed URL</div>
      <div class="step" id="s2"><div class="dot"></div> Fetch Encrypted Media Data</div>
      <div class="step" id="s3"><div class="dot"></div> Decrypt Final Stream</div>
    </div>
  </div>
  <div class="card">
    <label>Output <span class="badge" id="badge"></span></label>
    <div class="output" id="output">Results will appear here...</div>
  </div>
</div>
<script>
async function run() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  document.getElementById('output').textContent = 'Running...';
  document.getElementById('badge').textContent = '';
  ['s1','s2','s3'].forEach(id => document.getElementById(id).className = 'step');
  try {
    const resp = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ url: document.getElementById('url').value })
    });
    const data = await resp.json();
    data.steps.forEach((s,i) => document.getElementById('s'+(i+1)).classList.add(s.status));
    if (data.error) {
      document.getElementById('output').innerHTML = '<span class="error-msg">ERROR: ' + data.error + '</span>';
      document.getElementById('badge').textContent = 'FAILED';
    } else {
      document.getElementById('output').textContent = JSON.stringify(data.result, null, 2);
      document.getElementById('badge').textContent = 'SUCCESS';
    }
  } catch(e) {
    document.getElementById('output').innerHTML = '<span class="error-msg">' + e.message + '</span>';
  }
  btn.disabled = false;
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/run', methods=['POST'])
def run():
    url = request.json.get('url', '')
    steps = [{"status": "active"}, {"status": ""}, {"status": ""}]
    try:
        enc = requests.get(url, headers=HEADERS, timeout=15).json()["result"]
        dec = requests.post(f"{API}/dec-kai", json={"text": enc}, timeout=10).json()["result"]
        embed = dec["url"]
        steps[0]["status"] = "done"

        steps[1]["status"] = "active"
        referer = embed.split("/e/")[0] + "/"
        headers = {**HEADERS, "Referer": referer}
        media = embed.replace("/e/", "/media/")
        encrypted = requests.get(media, headers=headers, timeout=15).json()['result']
        steps[1]["status"] = "done"

        steps[2]["status"] = "active"
        dec_resp = requests.post(f"{API}/dec-mega", json={"text": encrypted, "agent": HEADERS["User-Agent"]}, timeout=10).json()
        if dec_resp.get("status") != 200:
            steps[2]["status"] = "error"
            return jsonify({"steps": steps, "error": dec_resp.get("error", "Decryption failed")})
        decrypted = dec_resp["result"]
        steps[2]["status"] = "done"

        return jsonify({"steps": steps, "result": decrypted, "referer": referer})
    except Exception as e:
        for s in steps:
            if s["status"] == "active":
                s["status"] = "error"
        return jsonify({"steps": steps, "error": str(e)})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
