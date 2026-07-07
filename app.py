import os
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import fireworks.client

load_dotenv()

app = Flask(__name__)
api_key = os.getenv("FIREWORKS_API_KEY")
print(f"API Key loaded: {api_key[:10]}..." if api_key else "NO API KEY FOUND!")
fireworks.client.api_key = api_key
if not api_key:
    fireworks.client.api_key = "fw_JYNA5cxjBEyM6DxZ9JsznA"

SYSTEM_PROMPT = """You are OlfactAI, an AI smell intelligence agent. 
Your job is to analyze smell descriptions and:
1. Classify the smell (floral, earthy, chemical, burnt, rotten, gas, etc.)
2. Detect danger level: SAFE, WARNING, or DANGER
3. If DANGER detected (especially LPG gas, smoke, chemical), give emergency instructions
4. Provide helpful recommendations

For LPG/gas leak indicators (sweet, rotten eggs, chemical smell in kitchen/home):
- ALWAYS classify as DANGER
- Give clear emergency steps in Bahasa Indonesia and English

Respond in JSON format:
{
  "smell_type": "...",
  "danger_level": "SAFE|WARNING|DANGER", 
  "description": "...",
  "recommendation": "...",
  "emergency_steps": ["step1", "step2"] // only if DANGER
}"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OlfactAI - AI Smell Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 30px;
            text-align: center;
            border-bottom: 2px solid #00d4ff33;
        }
        .logo { font-size: 2.5rem; font-weight: 900; color: #00d4ff; }
        .tagline { color: #888; margin-top: 5px; }
        .container { max-width: 800px; margin: 40px auto; padding: 0 20px; }
        .input-box {
            background: #1a1a2e;
            border: 1px solid #00d4ff33;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            background: #0d0d1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            color: #e0e0e0;
            font-size: 1rem;
            resize: vertical;
            min-height: 100px;
        }
        textarea:focus { outline: none; border-color: #00d4ff; }
        button {
            background: linear-gradient(135deg, #00d4ff, #0066ff);
            color: white;
            border: none;
            padding: 14px 40px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            width: 100%;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.85; }
        .result { 
            background: #1a1a2e;
            border-radius: 16px;
            padding: 30px;
            display: none;
        }
        .danger-badge {
            display: inline-block;
            padding: 6px 20px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        .SAFE { background: #00ff8822; color: #00ff88; border: 1px solid #00ff88; }
        .WARNING { background: #ffaa0022; color: #ffaa00; border: 1px solid #ffaa00; }
        .DANGER { background: #ff003322; color: #ff3355; border: 1px solid #ff3355; animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }
        .smell-type { font-size: 1.4rem; font-weight: 700; margin-bottom: 10px; color: #00d4ff; }
        .description { color: #aaa; line-height: 1.6; margin-bottom: 15px; }
        .recommendation { 
            background: #0d0d1a; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 3px solid #00d4ff;
            margin-bottom: 15px;
        }
        .emergency {
            background: #ff003311;
            border: 1px solid #ff3355;
            border-radius: 8px;
            padding: 15px;
        }
        .emergency h3 { color: #ff3355; margin-bottom: 10px; }
        .emergency ol { padding-left: 20px; }
        .emergency li { margin-bottom: 8px; line-height: 1.5; }
        .loading { text-align: center; padding: 30px; display: none; }
        .spinner {
            width: 40px; height: 40px;
            border: 3px solid #333;
            border-top-color: #00d4ff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .examples { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; }
        .example-btn {
            background: #0d0d1a;
            border: 1px solid #333;
            color: #888;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            cursor: pointer;
            width: auto;
            margin: 0;
        }
        .example-btn:hover { border-color: #00d4ff; color: #00d4ff; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">👃 OlfactAI</div>
        <div class="tagline">AI Smell Intelligence Agent — Detects danger before it's too late</div>
    </div>
    <div class="container">
        <div class="input-box">
            <h2 style="margin-bottom:15px; color:#00d4ff">Describe the smell you detect</h2>
            <textarea id="smellInput" placeholder="e.g. Ada bau manis menyengat di dapur saya..."></textarea>
            <div class="examples">
                <span style="color:#666; font-size:0.85rem; align-self:center">Try:</span>
                <button class="example-btn" onclick="setExample('Ada bau manis menyengat di dapur, seperti gas')">🔴 Gas bocor</button>
                <button class="example-btn" onclick="setExample('Bau daging yang agak aneh dan asam')">🟡 Makanan basi</button>
                <button class="example-btn" onclick="setExample('Bau tanah setelah hujan deras')">🟢 Petrichor</button>
                <button class="example-btn" onclick="setExample('Ada bau asap terbakar dari ruangan sebelah')">🔴 Asap kebakaran</button>
            </div>
            <button onclick="analyzeSmell()">🔍 Analyze Smell</button>
        </div>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="color:#666">Analyzing smell profile...</p>
        </div>
        <div class="result" id="result"></div>
    </div>
    <script>
        function setExample(text) {
            document.getElementById('smellInput').value = text;
        }
        async function analyzeSmell() {
            const input = document.getElementById('smellInput').value.trim();
            if (!input) return alert('Please describe the smell first!');
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            try {
                const res = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({smell: input})
                });
                const data = await res.json();
                displayResult(data);
            } catch(e) {
                alert('Error: ' + e.message);
            }
            document.getElementById('loading').style.display = 'none';
        }
        function displayResult(data) {
            const el = document.getElementById('result');
            let emergency = '';
            if (data.emergency_steps && data.emergency_steps.length > 0) {
                emergency = `<div class="emergency">
                    <h3>⚠️ EMERGENCY STEPS / LANGKAH DARURAT</h3>
                    <ol>${data.emergency_steps.map(s => `<li>${s}</li>`).join('')}</ol>
                </div>`;
            }
            el.innerHTML = `
                <span class="danger-badge ${data.danger_level}">${data.danger_level}</span>
                <div class="smell-type">🧪 ${data.smell_type}</div>
                <div class="description">${data.description}</div>
                <div class="recommendation">💡 ${data.recommendation}</div>
                ${emergency}
            `;
            el.style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    smell_description = data.get('smell', '')
    
    try:
        response = fireworks.client.ChatCompletion.create(
            model="accounts/fireworks/models/qwen3p7-plus",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this smell: {smell_description}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        import json
        result_text = response.choices[0].message.content
        # Clean JSON if wrapped in markdown
        result_text = result_text.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "smell_type": "Unknown",
            "danger_level": "WARNING", 
            "description": "Could not analyze smell properly.",
            "recommendation": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)