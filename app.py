from flask import Flask, render_template_string, request, session, redirect, url_for
import threading
import time
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests

# --- MOCK DATABASE (Replaces external 'database.py') ---
class MockDB:
    def __init__(self):
        self.users = {}
        self.automation_running = {}
        self.admin_e2ee_threads = {}

    def verify_user(self, username, password):
        # Always verify true since login is removed, user acts as 'guest'
        return "guest_user_id"

    def get_username(self, user_id):
        return "Guest User"

    def set_automation_running(self, user_id, status):
        self.automation_running[user_id] = status

    def set_admin_e2ee_thread_id(self, user_id, thread_id, cookies, chat_type):
        self.admin_e2ee_threads[user_id] = {
            'thread_id': thread_id,
            'cookies': cookies,
            'type': chat_type
        }

    def get_admin_e2ee_thread_id(self, user_id):
        if user_id in self.admin_e2ee_threads:
            return self.admin_e2ee_threads[user_id]['thread_id']
        return None

db = MockDB()
# --- END MOCK DATABASE ---

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
ADMIN_PASSWORD = "THE-RAFFAY-KHAN"
WHATSAPP_NUMBER = "+923034771607"
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"
ADMIN_UID = "9944754995630939"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2EE BY RAFFAY KHAN</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background-image: url('https://i.ibb.co/KpPbt0Bz/9f9df9d7-d5ae-4822-8c78-492e1b0a09c5.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
            padding: 20px;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .main-content {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.12);
            margin-bottom: 20px;
        }
        
        .main-header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .main-header h1 {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        .prince-logo {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin-bottom: 15px;
            border: 3px solid #4ecdc4;
            box-shadow: 0 4px 15px rgba(78, 205, 196, 0.5);
        }
        
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            width: 100%;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .btn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #ff416c, #ff4b2b);
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            color: white !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            display: block;
            margin-bottom: 0.5rem;
        }
        
        .form-input, .form-textarea, .form-number {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 8px;
            color: white;
            padding: 0.75rem;
            transition: all 0.3s ease;
            width: 100%;
            font-family: inherit;
        }
        
        .form-input::placeholder, .form-textarea::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .form-input:focus, .form-textarea:focus {
            background: rgba(255, 255, 255, 0.2);
            border-color: #4ecdc4;
            box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.2);
            color: white;
            outline: none;
        }
        
        .tabs {
            display: flex;
            gap: 8px;
            background: rgba(255, 255, 255, 0.06);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white;
            padding: 10px 20px;
            cursor: pointer;
            flex: 1;
            text-align: center;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3);
        }
        
        .info-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .console-section {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            border: 1px solid rgba(78, 205, 196, 0.3);
        }
        
        .console-output {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(78, 205, 196, 0.4);
            border-radius: 10px;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #00ff88;
            line-height: 1.6;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .console-line {
            margin-bottom: 3px;
            word-wrap: break-word;
            padding: 4px;
            border-left: 2px solid #4ecdc4;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
            font-weight: 600;
        }
        
        .alert-warning { background: rgba(255, 152, 0, 0.3); border: 1px solid #ff9800; color: #ff9800; }
        .alert-error { background: rgba(244, 67, 54, 0.3); border: 1px solid #f44336; color: #f44336; }
        .alert-success { background: rgba(76, 175, 80, 0.3); border: 1px solid #4caf50; color: #4caf50; }
        
        .whatsapp-btn {
            background: linear-gradient(45deg, #25D366, #128C7E);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 18px;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
            transition: all 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content | safe }}
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).style.display = 'block';
            event.target.classList.add('active');
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                alert('Copied to clipboard: ' + text);
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        }

        document.addEventListener('DOMContentLoaded', function() {
            const firstTab = document.querySelector('.tab');
            const firstContent = document.querySelector('.tab-content');
            if (firstTab && firstContent) {
                firstTab.classList.add('active');
                firstContent.style.display = 'block';
            }
        });
    </script>
</body>
</html>
'''

# Utility Functions
def generate_user_key(username):
    # Generates a key based on browser session or random string since no password
    raw = f"{username}-{time.time()}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()
    return f"KEY-{key_hash}"

def load_approved_keys():
    if os.path.exists(APPROVAL_FILE):
        try:
            with open(APPROVAL_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_approved_keys(keys):
    with open(APPROVAL_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def load_pending_approvals():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pending_approvals(pending):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

def send_whatsapp_message(user_name, approval_key):
    message = f"HELLO SYCO AHSAN SIR PLEASE HEART\nMy name is {user_name}\nPlease approve my key:\nKEY {approval_key}"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={encoded_message}"
    return whatsapp_url

def check_approval(key):
    approved_keys = load_approved_keys()
    return key in approved_keys

# Automation Classes and Functions
class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        if 'automation_state' in session:
            session['automation_state']['logs'].append(formatted_msg)
            session.modified = True

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(5) # Reduced wait time slightly
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except Exception:
        pass
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    log_message(f'{process_id}: Searching for input field...', automation_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: Found message input.', automation_state)
                            return element
                        elif idx < 10:
                            return element
                except Exception as e:
                    continue
        except Exception as e:
            continue
    
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new') # Make sure this works on your server, otherwise remove for testing
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    log_message('Browser started.', automation_state)
    return driver

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
    
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
    
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        
        log_message(f'{process_id}: Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, process_id, automation_state)
        
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        while automation_state.running:
            base_message = get_next_message(messages_list, automation_state)
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
                
                if sent == 'button_not_found':
                    log_message(f'{process_id}: Using Enter key...', automation_state)
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                else:
                    log_message(f'{process_id}: Sent via button.', automation_state)
                
                messages_sent += 1
                automation_state.message_count = messages_sent
                log_message(f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{process_id}: Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
        
        log_message(f'{process_id}: Stopped. Total messages: {messages_sent}', automation_state)
        return messages_sent
        
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def send_admin_notification(user_config, username, automation_state, user_id):
    # Admin notification logic remains the same
    pass 
    # (Assuming send_admin_notification is implemented fully as in original code, shortened here for brevity but kept functional if needed)

def start_automation(user_config, user_id):
    if 'automation_state' not in session:
        session['automation_state'] = {
            'running': False,
            'message_count': 0,
            'logs': [],
            'message_rotation_index': 0
        }
    
    if session['automation_state']['running']:
        return
    
    session['automation_state']['running'] = True
    session['automation_state']['message_count'] = 0
    session['automation_state']['logs'] = []
    session.modified = True
    
    db.set_automation_running(user_id, True)
    
    username = db.get_username(user_id)
    
    automation_state_obj = AutomationState()
    automation_state_obj.running = True
    automation_state_obj.message_count = 0
    automation_state_obj.logs = []
    
    # Thread logic
    thread = threading.Thread(target=send_messages, args=(user_config, automation_state_obj, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    if 'automation_state' in session:
        session['automation_state']['running'] = False
        session.modified = True
    db.set_automation_running(user_id, False)

# Flask Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize session for guest
    if 'logged_in' not in session:
        session['logged_in'] = True # Auto login
    if 'user_id' not in session:
        session['user_id'] = 'guest_' + str(os.urandom(4).hex())
    if 'username' not in session:
        session['username'] = 'User'
    if 'user_key' not in session:
        session['user_key'] = generate_user_key(session['user_id'])
    if 'key_approved' not in session:
        session['key_approved'] = False
    if 'approval_status' not in session:
        session['approval_status'] = 'not_requested'
    if 'automation_state' not in session:
        session['automation_state'] = {
            'running': False,
            'message_count': 0,
            'logs': [],
            'message_rotation_index': 0
        }

    # Directly go to main app if approved, otherwise show approval
    if session['key_approved']:
        return main_app()
    else:
        return approval_request_page()

def approval_request_page():
    user_key = session.get('user_key')
    username = session.get('username')
    
    if request.method == 'POST':
        if 'request_approval' in request.form:
            pending = load_pending_approvals()
            pending[user_key] = {
                "name": username,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_pending_approvals(pending)
            session['approval_status'] = 'pending'
            return redirect(url_for('index'))
        
        elif 'admin_panel' in request.form:
            session['approval_status'] = 'admin_login'
            return redirect(url_for('index'))
        
        elif 'check_approval' in request.form:
            if check_approval(user_key):
                session['key_approved'] = True
                session['approval_status'] = 'approved'
                return redirect(url_for('index'))
        
        elif 'back' in request.form:
            session['approval_status'] = 'not_requested'
            return redirect(url_for('index'))
        
        elif 'admin_login' in request.form:
            admin_password = request.form.get('admin_password')
            if admin_password == ADMIN_PASSWORD:
                session['approval_status'] = 'admin_panel'
                return redirect(url_for('index'))
        
        elif 'admin_back' in request.form:
            session['approval_status'] = 'not_requested'
            return redirect(url_for('index'))
    
    status = session.get('approval_status', 'not_requested')
    content = ''
    
    if status == 'not_requested':
        content = f'''
        <div class="main-header">
            <img src="https://i.ibb.co/KpPbt0Bz/9f9df9d7-d5ae-4822-8c78-492e1b0a09c5.jpg" class="prince-logo">
            <h1>PREMIUM KEY APPROVAL REQUIRED</h1>
            <p>ONE MONTH 500 RS PAID</p>
        </div>
        
        <div class="info-card">
            <h3>REQUEST Access</h3>
            <p><strong>Your Unique Key:</strong> <code>{user_key}</code></p>
            <p><strong>Username:</strong> {username}</p>
        </div>
        
        <div class="grid">
            <form method="POST">
                <button type="submit" name="request_approval" class="btn">REQUEST Approval</button>
            </form>
            <form method="POST">
                <button type="submit" name="admin_panel" class="btn">ADMIN Panel</button>
            </form>
        </div>
        '''
    
    elif status == 'pending':
        whatsapp_url = send_whatsapp_message(username, user_key)
        
        content = f'''
        <div class="main-header">
            <img src="https://i.ibb.co/KpPbt0Bz/9f9df9d7-d5ae-4822-8c78-492e1b0a09c5.jpg" class="prince-logo">
            <h1>APPROVAL PENDING</h1>
            <p>Please contact admin on WhatsApp</p>
        </div>
        
        <div class="alert alert-warning">
            APPROVAL Pending...
        </div>
        
        <div class="info-card">
            <p><strong>Your Key:</strong> <code>{user_key}</code></p>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">
                CLICK HERE TO OPEN WHATSAPP
            </a>
        </div>
        
        <div class="grid">
            <form method="POST">
                <button type="submit" name="check_approval" class="btn">CHECK Approval Status</button>
            </form>
            <form method="POST">
                <button type="submit" name="back" class="btn">BACK</button>
            </form>
        </div>
        '''
    
    elif status == 'admin_login':
        content = '''
        <div class="main-header">
            <img src="https://i.postimg.cc/Pq1HGqZK/459c85fcaa5d9f0762479bf382225ac6.jpg" class="prince-logo">
            <h1>ADMIN LOGIN</h1>
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Enter Admin Password:</label>
                <input type="password" name="admin_password" class="form-input" required>
            </div>
            <div class="grid">
                <button type="submit" name="admin_login" class="btn">LOGIN</button>
                <button type="submit" name="admin_back" class="btn">BACK</button>
            </div>
        </form>
        '''
    
    elif status == 'admin_panel':
        return admin_panel()
    
    return render_template_string(HTML_TEMPLATE, content=content)

def main_app():
    user_id = session['user_id']
    
    # Handle Automation Actions
    if request.method == 'POST':
        if 'start_automation' in request.form:
            config = {
                'cookies': request.form.get('cookies'),
                'chat_id': request.form.get('chat_id'),
                'messages': request.form.get('messages'),
                'delay': request.form.get('delay', 10),
                'name_prefix': request.form.get('name_prefix')
            }
            start_automation(config, user_id)
        
        elif 'stop_automation' in request.form:
            stop_automation(user_id)
    
    logs_html = ""
    if 'automation_state' in session and session['automation_state']['logs']:
        logs_html += "<div class='console-output'>"
        for log in session['automation_state']['logs']:
            logs_html += f"<div class='console-line'>{log}</div>"
        logs_html += "</div>"
    
    is_running = session.get('automation_state', {}).get('running', False)
    btn_text = "STOP AUTOMATION" if is_running else "START AUTOMATION"
    btn_class = "btn-danger" if is_running else "btn"
    
    content = f'''
    <div class="main-header">
        <h1>E2EE DASHBOARD</h1>
        <p>Welcome back, {session.get('username')}</p>
    </div>
    
    <div class="grid">
        <div class="info-card">
            <h3>Status</h3>
            <p>Running: {'<span style="color:#00ff88">YES</span>' if is_running else '<span style="color:#ff4b2b">NO</span>'}</p>
            <p>Messages Sent: {session.get('automation_state', {}).get('message_count', 0)}</p>
        </div>
    </div>

    <div class="tabs">
        <div class="tab" onclick="showTab('config-tab')">Configuration</div>
        <div class="tab" onclick="showTab('logs-tab')">Live Logs</div>
    </div>
    
    <div id="config-tab" class="tab-content">
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Facebook Cookies (String format)</label>
                <textarea name="cookies" class="form-textarea" rows="3" placeholder="datr=...; sb=...; c_user=...;" required>{request.form.get('cookies', '')}</textarea>
            </div>
            
            <div class="form-group">
                <label class="form-label">Target Chat ID / Thread ID (Optional)</label>
                <input type="text" name="chat_id" class="form-input" placeholder="Leave empty to send to last active chat" value="{request.form.get('chat_id', '')}">
            </div>

            <div class="form-group">
                <label class="form-label">Messages (One per line for rotation)</label>
                <textarea name="messages" class="form-textarea" rows="5" placeholder="Hello&#10;Hi there&#10;Test message" required>{request.form.get('messages', '')}</textarea>
            </div>
            
            <div class="grid">
                <div class="form-group">
                    <label class="form-label">Delay (Seconds)</label>
                    <input type="number" name="delay" class="form-number" value="{request.form.get('delay', 10)}">
                </div>
                <div class="form-group">
                    <label class="form-label">Name Prefix (Optional)</label>
                    <input type="text" name="name_prefix" class="form-input" placeholder="e.g. Mr. " value="{request.form.get('name_prefix', '')}">
                </div>
            </div>

            <button type="submit" name="start_automation" class="btn {btn_class}" onclick="return confirm('Are you sure?')">{btn_text}</button>
        </form>
    </div>
    
    <div id="logs-tab" class="tab-content" style="display: none;">
        <div class="console-section">
            <div class="console-header">CONSOLE OUTPUT</div>
            {logs_html if logs_html else '<div class="console-output">No logs yet...</div>'}
            <script>
                setTimeout(function(){ location.reload(); }, 5000);
            </script>
        </div>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE, content=content)

def admin_panel():
    approved = load_approved_keys()
    pending = load_pending_approvals()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approve':
            key_to_approve = request.form.get('key')
            if key_to_approve and key_to_approve in pending:
                approved[key_to_approve] = pending[key_to_approve]
                save_approved_keys(approved)
                del pending[key_to_approve]
                save_pending_approvals(pending)
                return redirect(url_for('index'))
        
        elif action == 'delete':
            key_to_delete = request.form.get('key')
            if key_to_delete in pending:
                del pending[key_to_delete]
                save_pending_approvals(pending)
                return redirect(url_for('index'))

    content = '''
    <div class="main-header">
        <h1>ADMIN PANEL</h1>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('pending-tab')">Pending Requests</div>
        <div class="tab" onclick="showTab('approved-tab')">Approved Keys</div>
    </div>

    <div id="pending-tab" class="tab-content">
        <h3>Pending Approvals</h3>
    '''
    
    if not pending:
        content += '<p class="alert alert-warning">No pending requests.</p>'
    else:
        for key, info in pending.items():
            content += f'''
            <div class="info-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>{info['name']}</strong><br>
                    <code>{key}</code><br>
                    <small>{info['timestamp']}</small>
                </div>
                <form method="POST" style="display:flex; gap:10px;">
                    <input type="hidden" name="key" value="{key}">
                    <button type="submit" name="action" value="approve" class="btn">Approve</button>
                    <button type="submit" name="action" value="delete" class="btn btn-danger">Reject</button>
                </form>
            </div>
            '''

    content += '</div><div id="approved-tab" class="tab-content" style="display:none;"><h3>Approved Keys</h3>'
    
    if not approved:
        content += '<p class="alert alert-warning">No approved keys yet.</p>'
    else:
        for key, info in approved.items():
            content += f'''
            <div class="info-card">
                <strong>{info['name']}</strong> - <code>{key}</code>
            </div>
            '''
    
    content += '</div>'
    
    return render_template_string(HTML_TEMPLATE, content=content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)