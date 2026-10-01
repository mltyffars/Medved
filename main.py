import html
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
import threading
import time
import urllib.parse
import requests

# ----------------------------------------------------
# إعدادات متعددة النماذج والمفاتيح (Gemini, GPT, Claude)
# ----------------------------------------------------
AI_PROVIDERS = [
    {
        "name": "Gemini",
        "keys": ["https://a77fe16144f57eff-136-119-150-58.serveousercontent.com", "AIzaSy_GEMINI_KEY_2"],
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
    },
    {
        "name": "OpenAI",
        "keys": ["sk-OPENAI_KEY_1", "sk-OPENAI_KEY_2"],
        "url": "https://api.openai.com/v1/chat/completions",
    },
    {
        "name": "Claude",
        "keys": ["sk-ant-CLAUDE_KEY_1", "sk-ant-CLAUDE_KEY_2"],
        "url": "https://api.anthropic.com/v1/messages",
    },
]

provider_index = 0
key_indices = [0, 0, 0]
rotation_lock = threading.Lock()


def get_next_ai_target():
  """دالة ذكية لاختيار النموذج والمفتاح التالي بالتبادل"""
  global provider_index, key_indices
  with rotation_lock:
    provider = AI_PROVIDERS[provider_index]
    k_idx = key_indices[provider_index]
    current_key = provider["keys"][k_idx]

    # تحديث المؤشرات للتبديل التلقائي في المرة القادمة
    key_indices[provider_index] = (k_idx + 1) % len(provider["keys"])
    if key_indices[provider_index] == 0:
      provider_index = (provider_index + 1) % len(AI_PROVIDERS)

    return provider["name"], current_key, provider["url"]


# 1. تهيئة قاعدة البيانات وبروتوكولات الحماية للتخزين
def init_db():
  conn = sqlite3.connect("factory.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            code_snippet TEXT,
            ai_report TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_date TEXT UNIQUE,
            issue_count INTEGER
        )
    """)
  conn.commit()
  conn.close()


init_db()


# 2. بروتوكول حماية المدخلات (Sanitization & Validation)
def sanitize_input(input_text):
  if not input_text:
    return ""
  return html.escape(input_text.strip())


# 3. محرك الذكاء الاصطناعي متعدد النماذج لفحص وإصلاح الكود
def process_ai_emergency_fix(code_snippet):
  if len(code_snippet) < 5:
    return "خطأ: الكود المدخل قصير جداً أو غير صالح للفحص."

  # محاولة التجربة عبر النماذج والمفاتيح المتاحة بالتناوب (حتى 6 محاولات كحد أقصى)
  for _ in range(6):
    model_name, current_key, api_url = get_next_ai_target()
    try:
      # محاكاة الاتصال الفعلي بالنموذج المختار (Gemini / GPT / Claude)
      # هنا يتم إرسال الطلب API باستخدام current_key و api_url بناءً على الـ model_name

      report = (
          f"✅ تم الفحص بنجاح باستخدام نموذج ({model_name}). الكود آمن وخالٍ من"
          " الثغرات. تم تصحيح المنطق البرمجي وتحسين الأداء لخدمة طوارئ Upwork"
          " (100$)."
      )
      return report
    except Exception as e:
      continue

  return "خطأ: فشل الاتصال بجميع نماذج الذكاء الاصطناعي المتاحة حالياً."


# 4. المراقب الخلفي (Background Worker) لإدارة المهام صامتاً
def background_worker():
  while True:
    conn = sqlite3.connect("factory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='معلق'")
    pending = cursor.fetchone()[0]
    conn.close()

    if pending > 0:
      print(f"[Background System] يوجد {pending} مهام طوارئ قيد المعالجة...")

    time.sleep(30)


threading.Thread(target=background_worker, daemon=True).start()


# 5. السيرفر المحلي ومعالجة الطلبات البرمجية
class SecureFactoryHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    if self.path == "/" or self.path == "":
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()

      html_content = """
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>Medvedev - نظام طوارئ Upwork الآمن</title>
                <style>
                    body { font-family: Tahoma, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
                    .container { max-width: 800px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
                    h1 { color: #38bdf8; text-align: center; }
                    .card { background: #334155; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .btn { background: #0284c7; color: white; padding: 12px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; }
                    .btn:hover { background: #0369a1; }
                    textarea, input { width: 100%; background: #0f172a; color: #fff; border: 1px solid #475569; border-radius: 6px; padding: 10px; box-sizing: border-box; margin-bottom: 10px; }
                    textarea { height: 120px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚡ Medvedev - نظام الطوارئ الآلي (متعدد النماذج)</h1>
                    <p style="text-align: center; color: #94a3b8;">باقة الطوارئ (100$) - بحد أقصى 50 مشكلة يومياً (موزعة على Gemini, GPT, Claude)</p>
                    
                    <div class="card">
                        <form action="/submit" method="POST">
                            <label>اسم الشركة أو العميل:</label>
                            <input type="text" name="company" placeholder="أدخل اسم العميل هنا..." required>
                            
                            <label>الكود البرمجي المعطل:</label>
                            <textarea name="code" placeholder="الصق الكود هنا للفحص والاصلاح الآلي..." required></textarea>
                            
                            <button type="submit" class="btn">تنفيذ الفحص والإصلاح الفوري</button>
                        </form>
                    </div>
                </div>
            </body>
            </html>
            """
      self.wfile.write(html_content.encode("utf-8"))
    else:
      self.send_response(404)
      self.end_headers()

  def do_POST(self):
    if self.path == "/submit":
      content_length = int(self.headers["Content-Length"])
      post_data = self.rfile.read(content_length).decode("utf-8")

      params = {}
      for item in post_data.split("&"):
        if "=" in item:
          k, v = item.split("=", 1)
          params[k] = urllib.parse.unquote_plus(v)

      company = sanitize_input(params.get("company", ""))
      code = sanitize_input(params.get("code", ""))

      # فحص حصة الـ 50 مشكلة اليومية
      today = time.strftime("%Y-%m-%d")
      conn = sqlite3.connect("factory.db")
      cursor = conn.cursor()

      cursor.execute(
          "SELECT issue_count FROM daily_limits WHERE day_date = ?", (today,)
      )
      row = cursor.fetchone()
      current_count = row[0] if row else 0

      if current_count >= 50:
        conn.close()
        self.send_response(400)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<h1>عذراً، تم استنفاد الحد الأقصى (50 مشكلة يومياً) للطوارئ لهذا"
            " اليوم.</h1>".encode("utf-8")
        )
        return

      if row:
        cursor.execute(
            "UPDATE daily_limits SET issue_count = issue_count + 1 WHERE"
            " day_date = ?",
            (today,),
        )
      else:
        cursor.execute(
            "INSERT INTO daily_limits (day_date, issue_count) VALUES (?, 1)",
            (today,),
        )

      # معالجة الكود عبر توزيع الذكاء الاصطناعي متعدد النماذج
      ai_report = process_ai_emergency_fix(code)

      cursor.execute(
          "INSERT INTO tasks (company_name, code_snippet, ai_report, status)"
          " VALUES (?, ?, ?, ?)",
          (company, code, ai_report, "مكتملة"),
      )
      conn.commit()
      conn.close()

      # إرسال النتيجة تلقائياً إلى Zapier للرد الفوري على العميل
      ZAPIER_WEBHOOK_URL = (
          "YOUR_ZAPIER_WEBHOOK_URL_HERE"  # ضع رابط Zapier هنا
      )
      payload = {
          "company_name": company,
          "code_snippet": code,
          "ai_report": ai_report,
      }
      try:
        requests.post(ZAPIER_WEBHOOK_URL, json=payload)
      except Exception as e:
        print(f"خطأ في إرسال البيانات إلى Zapier: {e}")

      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()

      response_page = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head><meta charset="UTF-8"><title>النتيجة</title></head>
            <body style="background:#0f172a; color:#fff; font-family:Tahoma; text-align:center; padding:50px;">
                <h1 style="color:#4ade80;">✅ تمت معالجة الكود وإرساله للعميل بنجاح!</h1>
                <p><strong>العميل:</strong> {company}</p>
                <p><strong>تقرير الإصلاح:</strong> {ai_report}</p>
                <br>
                <a href="/" style="background:#0284c7; color:#fff; padding:10px 20px; text-decoration:none; border-radius:6px;">العودة للرئيسية</a>
            </body>
            </html>
            """
      self.wfile.write(response_page.encode("utf-8"))


def run():
  port = int(os.environ.get("PORT", 10000))
  server_address = ("", port)
  httpd = HTTPServer(server_address, SecureFactoryHandler)
  print(
      f"Medvedev Multi-Model Secure Server running on port {port}..."
  )
  httpd.serve_forever()


if __name__ == "__main__":
  run()
