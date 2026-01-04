from flask import Flask, render_template_string, request, session, redirect, url_for
import threading
import time
import uuid
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import database as db
import requests

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
        
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;
            margin-top: 0.5rem;
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
        }
        
        .tab.active {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        }
        
        .metric-value {
            color: #4ecdc4;
            font-weight: 700;
            font-size: 1.8rem;
        }
        
        .metric-label {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
        }
        
        .console-section {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            border: 1px solid rgba(78, 205, 196, 0.3);
        }
        
        .console-header {
            color: #4ecdc4;
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .console-output {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(78, 205, 196, 0.4);
            border-radius: 10px;
            padding: 12px;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            color: #00ff88;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .console-line {
            margin-bottom: 3px;
            word-wrap: break-word;
            padding: 6px 10px;
            padding-left: 28px;
            color: #00ff88;
            background: rgba(78, 205, 196, 0.08);
            border-left: 2px solid rgba(78, 205, 196, 0.4);
            position: relative;
        }
        
        .console-line::before {
            content: '►';
            position: absolute;
            left: 10px;
            opacity: 0.6;
            color: #4ecdc4;
        }
        
        .success-box {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 1rem 0;
        }
        
        .error-box {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 1rem 0;
        }
        
        .info-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 600;
            margin-top: 3rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .whatsapp-btn {
            background: linear-gradient(45deg, #25D366, #128C7E);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 18px;
            display: inline-block;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
            transition: all 0.3s ease;
        }
        
        .whatsapp-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 211, 102, 0.6);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
        }
        
        .alert-success {
            background: rgba(76, 175, 80, 0.3);
            border: 1px solid rgba(76, 175, 80, 0.5);
            color: #4caf50;
        }
        
        .alert-error {
            background: rgba(244, 67, 54, 0.3);
            border: 1px solid rgba(244, 67, 54, 0.5);
            color: #f44336;
        }
        
        .alert-warning {
            background: rgba(255, 152, 0, 0.3);
            border: 1px solid rgba(255, 152, 0, 0.5);
            color: #ff9800;
        }
        
        .alert-info {
            background: rgba(33, 150, 243, 0.3);
            border: 1px solid rgba(33, 150, 243, 0.5);
            color: #2196f3;
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content | safe }}
    </div>
    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
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
        
        // Show first tab by default
        document.addEventListener('DOMContentLoaded', function() {
            const firstTab = document.querySelector('.tab');
            const firstTabContent = document.querySelector('.tab-content');
            if (firstTab && firstTabContent) {
                firstTab.classList.add('active');
                firstTabContent.style.display = 'block';
            }
        });
    </script>
</body>
</html>
'''

# Utility Functions
def generate_user_key(username, password):
    combined = f"{username}:{password}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
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
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{process_id}: Page Title: {page_title}', automation_state)
        log_message(f'{process_id}: Page URL: {page_url}', automation_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', automation_state)
    
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
    
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', automation_state)
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', automation_state)
            
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    
                    if is_editable:
                        log_message(f'{process_id}: Found editable element with selector #{idx+1}', automation_state)
                        
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                        
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: FOUND message input with text: {element_text[:50]}', automation_state)
                            return element
                        elif idx < 10:
                            log_message(f'{process_id}: FOUND Using primary selector editable element (#{idx+1})', automation_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{process_id}: FOUND Using fallback editable element', automation_state)
                            return element
                except Exception as e:
                    log_message(f'{process_id}: Element check failed: {str(e)[:50]}', automation_state)
                    continue
        except Exception as e:
            continue
    
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', automation_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', automation_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', automation_state)
    except Exception:
        pass
    
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', automation_state)
            break
    
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', automation_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', automation_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', automation_state)
        
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

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
                    log_message(f'{process_id}: Send button not found, using Enter key...', automation_state)
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
                    log_message(f'{process_id}: SENT via Enter: "{message_to_send[:30]}..."', automation_state)
                else:
                    log_message(f'{process_id}: SENT via button: "{message_to_send[:30]}..."', automation_state)
                
                messages_sent += 1
                automation_state.message_count = messages_sent
                
                log_message(f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{process_id}: Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
        
        log_message(f'{process_id}: Automation stopped. Total messages: {messages_sent}', automation_state)
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
    driver = None
    try:
        log_message(f"ADMIN-NOTIFY: Preparing admin notification...", automation_state)
        
        admin_e2ee_thread_id = db.get_admin_e2ee_thread_id(user_id)
        
        if admin_e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Using saved admin thread: {admin_e2ee_thread_id}", automation_state)
        
        driver = setup_browser(automation_state)
        
        log_message(f"ADMIN-NOTIFY: Navigating to Facebook...", automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if user_config['cookies'] and user_config['cookies'].strip():
            log_message(f"ADMIN-NOTIFY: Adding cookies...", automation_state)
            cookie_array = user_config['cookies'].split(';')
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
        
        user_chat_id = user_config.get('chat_id', '')
        admin_found = False
        e2ee_thread_id = admin_e2ee_thread_id
        chat_type = 'REGULAR'
        
        if e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Opening saved admin conversation...", automation_state)
            
            if '/e2ee/' in str(e2ee_thread_id) or admin_e2ee_thread_id:
                conversation_url = f'https://www.facebook.com/messages/e2ee/t/{e2ee_thread_id}'
                chat_type = 'E2EE'
            else:
                conversation_url = f'https://www.facebook.com/messages/t/{e2ee_thread_id}'
                chat_type = 'REGULAR'
            
            log_message(f"ADMIN-NOTIFY: Opening {chat_type} conversation: {conversation_url}", automation_state)
            driver.get(conversation_url)
            time.sleep(8)
            admin_found = True
        
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Searching for admin UID: {ADMIN_UID}...", automation_state)
            
            try:
                profile_url = f'https://www.facebook.com/{ADMIN_UID}'
                log_message(f"ADMIN-NOTIFY: Opening admin profile: {profile_url}", automation_state)
                driver.get(profile_url)
                time.sleep(8)
                
                message_button_selectors = [
                    'div[aria-label*="Message" i]',
                    'a[aria-label*="Message" i]',
                    'div[role="button"]:has-text("Message")',
                    'a[role="button"]:has-text("Message")',
                    '[data-testid*="message"]'
                ]
                
                message_button = None
                for selector in message_button_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            for elem in elements:
                                text = elem.text.lower() if elem.text else ""
                                aria_label = elem.get_attribute('aria-label') or ""
                                if 'message' in text or 'message' in aria_label.lower():
                                    message_button = elem
                                    log_message(f"ADMIN-NOTIFY: Found message button: {selector}", automation_state)
                                    break
                            if message_button:
                                break
                    except:
                        continue
                
                if message_button:
                    log_message(f"ADMIN-NOTIFY: Clicking message button...", automation_state)
                    driver.execute_script("arguments[0].click();", message_button)
                    time.sleep(8)
                    
                    current_url = driver.current_url
                    log_message(f"ADMIN-NOTIFY: Redirected to: {current_url}", automation_state)
                    
                    if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                        if '/e2ee/t/' in current_url:
                            e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'E2EE'
                            log_message(f"ADMIN-NOTIFY: FOUND E2EE conversation: {e2ee_thread_id}", automation_state)
                        else:
                            e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'REGULAR'
                            log_message(f"ADMIN-NOTIFY: FOUND REGULAR conversation: {e2ee_thread_id}", automation_state)
                        
                        if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                            current_cookies = user_config.get('cookies', '')
                            db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                            admin_found = True
                    else:
                        log_message(f"ADMIN-NOTIFY: Message button didn't redirect to messages page", automation_state)
                else:
                    log_message(f"ADMIN-NOTIFY: Could not find message button on profile", automation_state)
            
            except Exception as e:
                log_message(f"ADMIN-NOTIFY: Profile approach failed: {str(e)[:100]}", automation_state)
            
            if not admin_found or not e2ee_thread_id:
                log_message(f"ADMIN-NOTIFY: COULD NOT FIND admin via search, trying DIRECT MESSAGE approach...", automation_state)
                
                try:
                    profile_url = f'https://www.facebook.com/messages/new'
                    log_message(f"ADMIN-NOTIFY: Opening new message page...", automation_state)
                    driver.get(profile_url)
                    time.sleep(8)
                    
                    search_box = None
                    search_selectors = [
                        'input[aria-label*="To:" i]',
                        'input[placeholder*="Type a name" i]',
                        'input[type="text"]'
                    ]
                    
                    for selector in search_selectors:
                        try:
                            search_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if search_elements:
                                for elem in search_elements:
                                    if elem.is_displayed():
                                        search_box = elem
                                        log_message(f"ADMIN-NOTIFY: Found 'To:' box with: {selector}", automation_state)
                                        break
                                if search_box:
                                    break
                        except:
                            continue
                    
                    if search_box:
                        log_message(f"ADMIN-NOTIFY: Typing admin UID in new message...", automation_state)
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        """, search_box, ADMIN_UID)
                        time.sleep(5)
                        
                        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"], li[role="option"], a[role="option"]')
                        if result_elements:
                            log_message(f"ADMIN-NOTIFY: Found {len(result_elements)} results, clicking first...", automation_state)
                            driver.execute_script("arguments[0].click();", result_elements[0])
                            time.sleep(8)
                            
                            current_url = driver.current_url
                            if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                                if '/e2ee/t/' in current_url:
                                    e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'E2EE'
                                    log_message(f"ADMIN-NOTIFY: FOUND Direct message opened E2EE: {e2ee_thread_id}", automation_state)
                                else:
                                    e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'REGULAR'
                                    log_message(f"ADMIN-NOTIFY: FOUND Direct message opened REGULAR chat: {e2ee_thread_id}", automation_state)
                                
                                if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                                    admin_found = True
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Direct message approach failed: {str(e)[:100]}", automation_state)
        
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: ALL APPROACHES FAILED - Could not find/open admin conversation", automation_state)
            return
        
        conversation_type = "E2EE" if "e2ee" in driver.current_url else "REGULAR"
        log_message(f"ADMIN-NOTIFY: SUCCESSFULLY opened {conversation_type} conversation with admin", automation_state)
        
        message_input = find_message_input(driver, 'ADMIN-NOTIFY', automation_state)
        
        if message_input:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conversation_type = "E2EE LOCKED" if "e2ee" in driver.current_url.lower() else "Regular CHAT"
            notification_msg = f"NEW User Started Automation\n\nUSERNAME: {username}\nTIME: {current_time}\nCHAT TYPE: {conversation_type}\nTHREAD ID: {e2ee_thread_id if e2ee_thread_id else 'N/A'}"
            
            log_message(f"ADMIN-NOTIFY: Typing notification message...", automation_state)
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
            """, message_input, notification_msg)
            
            time.sleep(1)
            
            log_message(f"ADMIN-NOTIFY: Trying to send message...", automation_state)
            send_result = driver.execute_script("""
                const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                
                for (let btn of sendButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return 'button_clicked';
                    }
                }
                return 'button_not_found';
            """)
            
            if send_result == 'button_not_found':
                log_message(f"ADMIN-NOTIFY: Send button not found, using Enter key...", automation_state)
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
                log_message(f"ADMIN-NOTIFY: SENT via Enter key", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: SENT Send button clicked", automation_state)
            
            time.sleep(2)
        else:
            log_message(f"ADMIN-NOTIFY: FAILED to find message input", automation_state)
            
    except Exception as e:
        log_message(f"ADMIN-NOTIFY: ERROR sending notification: {str(e)}", automation_state)
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f"ADMIN-NOTIFY: Browser closed", automation_state)
            except:
                pass

def run_automation_with_notification(user_config, username, automation_state, user_id):
    send_admin_notification(user_config, username, automation_state, user_id)
    send_messages(user_config, automation_state, user_id)

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
    
    # Create AutomationState object for thread
    automation_state_obj = AutomationState()
    automation_state_obj.running = True
    automation_state_obj.message_count = 0
    automation_state_obj.logs = []
    
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state_obj, user_id))
    thread.daemon = True
    thread.start()
    
    # Store reference in session
    session['automation_thread_state'] = {
        'running': True,
        'message_count': 0,
        'logs': []
    }

def stop_automation(user_id):
    if 'automation_state' in session:
        session['automation_state']['running'] = False
        session.modified = True
    db.set_automation_running(user_id, False)

# Flask Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'logged_in' not in session:
        session['logged_in'] = False
    if 'user_id' not in session:
        session['user_id'] = None
    if 'username' not in session:
        session['username'] = None
    if 'user_key' not in session:
        session['user_key'] = None
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
    
    if not session['logged_in']:
        return login_page()
    elif not session['key_approved']:
        return approval_request_page()
    else:
        return main_app()

def login_page():
    if request.method == 'POST':
        if 'login' in request.form:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username and password:
                user_id = db.verify_user(username, password)
                if user_id:
                    user_key = generate_user_key(username, password)
                    
                    session['logged_in'] = True
                    session['user_id'] = user_id
                    session['username'] = username
                    session['user_key'] = user_key
                    
                    if check_approval(user_key):
                        session['key_approved'] = True
                        session['approval_status'] = 'approved'
                    else:
                        session['key_approved'] = False
                        session['approval_status'] = 'not_requested'
                    
                    return redirect(url_for('index'))
        
        elif 'signup' in request.form:
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = db.create_user(new_username, new_password)
                    if success:
                        return redirect(url_for('index'))
    
    content = '''
    <div class="main-header">
        <img src="https://raw.githubusercontent.com/rafaykhan72242/myimage/main/1764140169030.jpg" class="Raffay-logo">
        <h1>THE RAFFFAY OFFLINE E2EE</h1>
        <p>seven billion smiles in his world but yours is my favourite</p>
    </div>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('login-tab')">LOGIN</div>
        <div class="tab" onclick="showTab('signup-tab')">SIGN UP</div>
    </div>
    
    <div id="login-tab" class="tab-content">
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-input" placeholder="Enter your username" required>
            </div>
            <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-input" placeholder="Enter your password" required>
            </div>
            <button type="submit" name="login" class="btn">Login</button>
        </form>
    </div>
    
    <div id="signup-tab" class="tab-content" style="display: none;">
        <form method="POST">
            <div class="form-group">
                <label class="form-label">Choose Username</label>
                <input type="text" name="new_username" class="form-input" placeholder="Choose a unique username" required>
            </div>
            <div class="form-group">
                <label class="form-label">Choose Password</label>
                <input type="password" name="new_password" class="form-input" placeholder="Create a strong password" required>
            </div>
            <div class="form-group">
                <label class="form-label">Confirm Password</label>
                <input type="password" name="confirm_password" class="form-input" placeholder="Re-enter your password" required>
            </div>
            <button type="submit" name="signup" class="btn">Create Account</button>
        </form>
    </div>
    '''
    
    return render_template_string(HTML_TEMPLATE, content=content)

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
    content = ''  # ✅ YEH LINE ADD KARO - pehle hi initialize karo
    
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
            <img src="https://i.ibb.co/KpPbt0Bz/9f9df9d7-d5ae-4822-8c78-492e1b0a09c5.jpg" class="Raffay-logo">
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
        
        <div class="info-card">
            <h3>MESSAGE Preview:</h3>
            <div class="console-output">
                HELLO RAFFAY SIR PLEASE HEART<br>
                My name is {username}<br>
                Please approve my key:<br>
                KEY {user_key}
            </div>
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
    
    else:
        # ✅ Agar koi aur status ho to default page show karo
        content = f'''
        <div class="alert alert-error">
            <h3>ERROR: Unknown Status</h3>
            <p>Status: {status}</p>
            <p>Please go back to login</p>
        </div>
        <form method="POST">
            <button type="submit" name="back" class="btn">GO BACK</button>
        </form>
        '''
    
    return render_template_string(HTML_TEMPLATE, content=content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
