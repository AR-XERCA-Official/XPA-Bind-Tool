# ============================================================
# DROGON BIND TOOL - WEB VERSION
# FastAPI Backend
# ============================================================

import requests
import os
import sys
import json
import time
import urllib.parse
import base64
import hashlib
import urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# Protobuf imports
# ============================================================
try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    print("\n[!] Error: Protobuf files not found!")
    sys.exit()

# ============================================================
# FastAPI App Setup
# ============================================================
app = FastAPI(title="AbdoX BIND TOOL", version="3.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# ============================================================
# ============================================================
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

def enc(d):
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def dec(d):
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

# ============================================================
# Constants
# ============================================================
PLATFORM_MAP = {
    1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line",
    11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
}

# ============================================================
# Helper Functions
# ============================================================
def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def format_response_result(response_text):
    """تنسيق الرد من API بشكل مبسط"""
    try:
        parsed = json.loads(response_text)
        result_code = parsed.get("result")
        if result_code == 0:
            return {"status": "success", "message": "SUCCESS", "data": parsed}
        elif result_code is not None:
            error_msg = parsed.get("error", "Unknown error")
            return {"status": "error", "code": result_code, "message": error_msg, "data": parsed}
        else:
            return {"status": "info", "message": "Completed", "data": parsed}
    except:
        if '"result": 0' in response_text.replace(" ", ""):
            return {"status": "success", "message": "SUCCESS", "data": {"raw": response_text}}
        else:
            return {"status": "error", "message": "Unrecognized response", "data": {"raw": response_text}}

def read_varint(data, offset):
    res = 0
    shift = 0
    while True:
        if offset >= len(data):
            break
        b = data[offset]
        offset += 1
        res |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res, offset

def parse_record(data):
    rec = {}
    offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0:
            val, offset = read_varint(data, offset)
            if f == 1:
                rec['ts'] = val
            elif f == 2:
                rec['ram'] = val
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]
            offset += length
            if f == 3:
                rec['dev'] = val.decode(errors='ignore')
            elif f == 4:
                rec['arch'] = val.decode(errors='ignore')
        else:
            break
    return rec

def parse_history_protobuf(data):
    records = []
    offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0:
            val, offset = read_varint(data, offset)
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]
            offset += length
            if f == 1:
                records.append(parse_record(val))
        else:
            break
    return records

def build_majorlogin(tok, open_id, p_type):
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.120.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())
    # ============================================================
# API ENDPOINTS - PART 1
# Bind Info + Bind Email
# ============================================================

# ============================================================
# 1. CHECK BIND INFO
# ============================================================
@app.post("/api/bind-info")
async def api_bind_info(access_token: str = Form(...)):
    """
    فحص معلومات الربط للحساب
    """
    result = {
        "success": False,
        "player": {},
        "bind": {},
        "error": None
    }
    
    try:
        # جلب بيانات اللاعب
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        p_res = requests.get(player_url, headers=headers, timeout=15, allow_redirects=True)
        parsed_url = urllib.parse.urlparse(p_res.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        result["player"] = {
            "uid": query_params.get("account_id", ["Unknown"])[0],
            "nickname": urllib.parse.unquote(query_params.get("nickname", ["Unknown"])[0]),
            "region": query_params.get("region", ["Unknown"])[0]
        }
        
        # جلب معلومات الربط
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {"app_id": "100067", "access_token": access_token}
        response = requests.get(url, params=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            email = data.get("email", "")
            email_to_be = data.get("email_to_be", "")
            countdown = data.get("request_exec_countdown", 0)
            result_code = data.get("result", -1)
            
            result["bind"] = {
                "email": email,
                "email_to_be": email_to_be,
                "countdown": countdown,
                "countdown_human": convert_seconds(countdown) if countdown else "",
                "result_code": result_code,
                "success": result_code == 0
            }
            
            # Summary
            if email == "" and email_to_be != "":
                result["bind"]["summary"] = f"Pending email confirmation: {email_to_be} - Confirms in: {convert_seconds(countdown)}"
            elif email != "" and email_to_be == "":
                result["bind"]["summary"] = f"Email confirmed: {email}"
            elif email == "" and email_to_be == "":
                result["bind"]["summary"] = "No recovery email set"
            else:
                result["bind"]["summary"] = f"Current: {email} | Pending: {email_to_be}"
            
            result["success"] = True
        else:
            result["error"] = f"API Error (Status {response.status_code})"
            
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 2. BIND EMAIL
# ============================================================
class BindEmailRequest(BaseModel):
    access_token: str
    email: str
    otp: str
    security_code: str
    verifier_token: Optional[str] = None

@app.post("/api/bind-email/send-otp")
async def api_bind_send_otp(access_token: str = Form(...), email: str = Form(...)):
    """
    إرسال OTP للإيميل الجديد
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {
        "email": email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    
    try:
        resp = requests.post(send_otp_url, headers=headers, data=send_otp_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/bind-email/verify-otp")
async def api_bind_verify_otp(
    access_token: str = Form(...),
    email: str = Form(...),
    otp: str = Form(...)
):
    """
    التحقق من OTP
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    verify_data = {
        "app_id": "100067",
        "access_token": access_token,
        "email": email,
        "code": otp,
        "otp": otp,
        "type": "1"
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        # استخراج verifier_token
        try:
            verifier_token = resp.json().get("verifier_token", "")
            if verifier_token:
                result["verifier_token"] = verifier_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/bind-email/finalize")
async def api_bind_finalize(
    access_token: str = Form(...),
    email: str = Form(...),
    verifier_token: str = Form(...),
    security_code: str = Form(...)
):
    """
    تنفيذ عملية الربط النهائية
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    bind_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "verifier_token": verifier_token,
        "secondary_password": security_code
    }
    
    try:
        resp = requests.post(bind_url, headers=headers, data=bind_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ============================================================
# 3. UNBIND EMAIL
# ============================================================
@app.post("/api/unbind-email/get-info")
async def api_unbind_get_info(access_token: str = Form(...)):
    """
    جلب معلومات الإيميل المرتبط لفك الربط
    """
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {"app_id": "100067", "access_token": access_token}
        info_headers = {"User-Agent": "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        data = r_info.json()
        email = data.get("email", "")
        
        if email:
            return JSONResponse({"status": "success", "email": email})
        else:
            return JSONResponse({"status": "error", "message": "No email bound to this account"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/unbind-email/send-otp")
async def api_unbind_send_otp(access_token: str = Form(...), email: str = Form(...)):
    """
    إرسال OTP للإيميل المرتبط لفك الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {
        "email": email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    
    try:
        resp = requests.post(send_otp_url, headers=headers, data=send_otp_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/unbind-email/verify-identity-otp")
async def api_unbind_verify_identity_otp(
    access_token: str = Form(...),
    email: str = Form(...),
    otp: str = Form(...)
):
    """
    التحقق من الهوية باستخدام OTP لفك الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    verify_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "otp": otp
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        try:
            identity_token = resp.json().get("identity_token", "")
            if identity_token:
                result["identity_token"] = identity_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/unbind-email/verify-identity-code")
async def api_unbind_verify_identity_code(
    access_token: str = Form(...),
    email: str = Form(...),
    security_code: str = Form(...)
):
    """
    التحقق من الهوية باستخدام كود الأمان لفك الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    hashed_sec_code = hashlib.sha256(security_code.encode('utf-8')).hexdigest()
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    verify_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "secondary_password": hashed_sec_code
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        try:
            identity_token = resp.json().get("identity_token", "")
            if identity_token:
                result["identity_token"] = identity_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/unbind-email/finalize")
async def api_unbind_finalize(
    access_token: str = Form(...),
    identity_token: str = Form(...)
):
    """
    تنفيذ عملية فك الربط النهائية
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    unbind_url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    unbind_data = {
        "app_id": "100067",
        "access_token": access_token,
        "identity_token": identity_token
    }
    
    try:
        resp = requests.post(unbind_url, headers=headers, data=unbind_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
        # ============================================================
# API ENDPOINTS - PART 2
# Change Bind + Cancel Bind + EAT to Token
# ============================================================

# ============================================================
# 4. CHANGE BIND EMAIL
# ============================================================
@app.post("/api/change-bind/get-info")
async def api_change_get_info(access_token: str = Form(...)):
    """
    جلب معلومات الإيميل الحالي لتغيير الربط
    """
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {"app_id": "100067", "access_token": access_token}
        info_headers = {"User-Agent": "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        data = r_info.json()
        email = data.get("email", "")
        
        if email:
            return JSONResponse({"status": "success", "email": email})
        else:
            return JSONResponse({"status": "error", "message": "No email bound to this account"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/change-bind/verify-identity-otp")
async def api_change_verify_identity_otp(
    access_token: str = Form(...),
    email: str = Form(...),
    otp: str = Form(...)
):
    """
    التحقق من الهوية باستخدام OTP لتغيير الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    verify_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "otp": otp
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        try:
            identity_token = resp.json().get("identity_token", "")
            if identity_token:
                result["identity_token"] = identity_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/change-bind/verify-identity-code")
async def api_change_verify_identity_code(
    access_token: str = Form(...),
    email: str = Form(...),
    security_code: str = Form(...)
):
    """
    التحقق من الهوية باستخدام كود الأمان لتغيير الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    hashed_sec_code = hashlib.sha256(security_code.encode('utf-8')).hexdigest()
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    verify_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "secondary_password": hashed_sec_code
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        try:
            identity_token = resp.json().get("identity_token", "")
            if identity_token:
                result["identity_token"] = identity_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/change-bind/send-otp-new")
async def api_change_send_otp_new(
    access_token: str = Form(...),
    new_email: str = Form(...)
):
    """
    إرسال OTP للإيميل الجديد لتغيير الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {
        "email": new_email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    
    try:
        resp = requests.post(send_otp_url, headers=headers, data=send_otp_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/change-bind/verify-otp-new")
async def api_change_verify_otp_new(
    access_token: str = Form(...),
    new_email: str = Form(...),
    otp: str = Form(...)
):
    """
    التحقق من OTP للإيميل الجديد لتغيير الربط
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    verify_data = {
        "email": new_email,
        "app_id": "100067",
        "access_token": access_token,
        "otp": otp
    }
    
    try:
        resp = requests.post(verify_url, headers=headers, data=verify_data, timeout=15)
        result = format_response_result(resp.text)
        
        try:
            verifier_token = resp.json().get("verifier_token", "")
            if verifier_token:
                result["verifier_token"] = verifier_token
        except:
            pass
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/api/change-bind/finalize")
async def api_change_finalize(
    access_token: str = Form(...),
    identity_token: str = Form(...),
    new_email: str = Form(...),
    verifier_token: str = Form(...)
):
    """
    تنفيذ عملية تغيير الربط النهائية
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    rebind_url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    rebind_data = {
        "identity_token": identity_token,
        "email": new_email,
        "app_id": "100067",
        "verifier_token": verifier_token,
        "access_token": access_token
    }
    
    try:
        resp = requests.post(rebind_url, headers=headers, data=rebind_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ============================================================
# 5. CANCEL BIND REQUEST
# ============================================================
@app.post("/api/cancel-bind")
async def api_cancel_bind(access_token: str = Form(...)):
    """
    إلغاء طلب الربط المعلق
    """
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    cancel_url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    cancel_data = {
        "app_id": "100067",
        "access_token": access_token
    }
    
    try:
        resp = requests.post(cancel_url, headers=headers, data=cancel_data, timeout=15)
        result = format_response_result(resp.text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ============================================================
# 6. EAT TO ACCESS TOKEN
# ============================================================
@app.post("/api/eat-to-token")
async def api_eat_to_token(eat_input: str = Form(...)):
    """
    تحويل EAT Token إلى Access Token
    """
    result = {
        "success": False,
        "access_token": None,
        "player": {},
        "error": None
    }
    
    try:
        eat_token = None
        
        # استخراج EAT من الرابط أو النص
        if "http" in eat_input or "?" in eat_input:
            parsed_url = urllib.parse.urlparse(eat_input)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'eat' in query_params:
                eat_token = query_params['eat'][0]
        else:
            eat_token = eat_input.strip()
        
        if not eat_token:
            result["error"] = "Could not find EAT token"
            return JSONResponse(result)
        
        # الاتصال بالسيرفر
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36"
        }
        
        response = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(response.url)
        final_params = urllib.parse.parse_qs(parsed_final.query)
        
        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            result["success"] = True
            result["access_token"] = access_token
            result["player"] = {
                "account_id": final_params.get('account_id', ['Unknown'])[0],
                "nickname": urllib.parse.unquote(final_params.get('nickname', ['Unknown'])[0]),
                "region": final_params.get('region', ['Unknown'])[0]
            }
        else:
            result["error"] = "Access token not found. Token might be expired or invalid."
            
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 7. REVOKE ACCESS TOKEN
# ============================================================
@app.post("/api/revoke-token")
async def api_revoke_token(access_token: str = Form(...)):
    """
    إلغاء صلاحية Access Token
    """
    result = {
        "success": False,
        "player": {},
        "error": None
    }
    
    try:
        # التحقق من صحة التوكن
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'access_token' not in params:
            result["error"] = "Token is already invalid, expired, or revoked!"
            return JSONResponse(result)
        
        nickname = urllib.parse.unquote(params.get('nickname', ['Unknown'])[0])
        account_id = params.get('account_id', ['Unknown'])[0]
        region = params.get('region', ['Unknown'])[0]
        
        result["player"] = {
            "nickname": nickname,
            "account_id": account_id,
            "region": region
        }
        
        # تنفيذ عملية الإلغاء
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        
        logout_res = requests.get(logout_url, headers=headers, timeout=15)
        
        if logout_res.status_code == 200 and "error" not in logout_res.text:
            result["success"] = True
            result["message"] = "Successfully logged out & revoked"
        else:
            result["error"] = "Failed to revoke token"
            
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)
    # ============================================================
# API ENDPOINTS - PART 3
# Login History + Bound Accounts + Token to JWT + Ban
# ============================================================

# ============================================================
# 8. GET LOGIN HISTORY
# ============================================================
@app.post("/api/login-history")
async def api_login_history(token: str = Form(...)):
    """
    جلب سجل الدخول للحساب
    """
    result = {
        "success": False,
        "player": {},
        "history": [],
        "error": None
    }
    
    try:
        jwt_token = None
        open_id = None
        
        # التحقق إذا كان JWT
        if token.startswith("ey") and "." in token:
            jwt_token = token
            result["message"] = "Using JWT token directly"
        else:
            # استخراج Open ID من Access Token
            try:
                r = requests.get(
                    f"https://100067.connect.garena.com/oauth/token/inspect?token={token}",
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=5
                ).json()
                open_id = r.get("open_id")
            except:
                pass
            
            if not open_id:
                try:
                    uid_headers = {"access-token": token, "user-agent": "Mozilla/5.0"}
                    uid_res = requests.get(
                        "https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/",
                        headers=uid_headers,
                        verify=False,
                        timeout=5
                    ).json()
                    uid = uid_res.get("uid")
                    if uid:
                        openid_res = requests.post(
                            "https://topup.pk/api/auth/player_id_login",
                            json={"app_id": 100067, "login_id": str(uid)},
                            verify=False,
                            timeout=5
                        ).json()
                        open_id = openid_res.get("open_id")
                except:
                    pass
            
            if not open_id:
                result["error"] = "Failed to extract Open ID. Token is invalid or expired."
                return JSONResponse(result)
            
            # تجربة منصات مختلفة لـ MajorLogin
            platforms = [8, 3, 4, 6]
            for p_type in platforms:
                try:
                    pl = build_majorlogin(token, open_id, p_type)
                    mLhDr = {
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
                        "Connection": "Keep-Alive",
                        "Accept-Encoding": "gzip",
                        "Content-Type": "application/octet-stream",
                        "Expect": "100-continue",
                        "X-GA": "v1 1",
                        "X-Unity-Version": "2018.4.11f1",
                        "ReleaseVersion": "OB52"
                    }
                    x = requests.post(
                        "https://loginbp.ggpolarbear.com/MajorLogin",
                        headers=mLhDr,
                        data=pl,
                        timeout=10,
                        verify=False
                    )
                    if x.status_code == 200:
                        res = mLrPb.MajorLoginRes()
                        try:
                            res.ParseFromString(dec(x.content))
                        except:
                            res.ParseFromString(x.content)
                        if res.token:
                            jwt_token = res.token
                            break
                except:
                    continue
        
        if not jwt_token:
            result["error"] = "MajorLogin failed. Token might be blocked."
            return JSONResponse(result)
        
        # استخراج معلومات اللاعب من JWT
        try:
            payload_b64 = jwt_token.split('.')[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            
            result["player"] = {
                "nickname": urllib.parse.unquote(decoded.get("nickname", "Unknown")),
                "account_id": decoded.get("account_id", "Unknown"),
                "region": decoded.get("lock_region", "Unknown"),
                "platform": PLATFORM_MAP.get(decoded.get("external_type", 0), "Unknown")
            }
        except:
            pass
        
        # جلب سجل الدخول
        hH = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB52",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)",
            "Host": "client.ind.freefiremobile.com",
            "Connection": "close"
        }
        
        r = requests.post(
            "https://client.ind.freefiremobile.com/GetLoginHistory",
            headers=hH,
            data=enc(b""),
            timeout=15,
            verify=False
        )
        
        if r.status_code != 200:
            result["error"] = f"History Request Failed: HTTP {r.status_code}"
            return JSONResponse(result)
        
        try:
            d = dec(r.content)
        except:
            d = r.content
        
        records = parse_history_protobuf(d)
        
        for rec in records:
            ts_raw = rec.get('ts', 0)
            try:
                date_str = datetime.fromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S')
            except:
                date_str = "Invalid Format"
            
            result["history"].append({
                "timestamp": ts_raw,
                "date": date_str,
                "device": rec.get('dev', 'Unknown Device'),
                "architecture": rec.get('arch', 'Unknown Architecture'),
                "ram": rec.get('ram', 0)
            })
        
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 9. CHECK BOUND ACCOUNTS (Platform Bind Info)
# ============================================================
@app.post("/api/bound-accounts")
async def api_bound_accounts(access_token: str = Form(...)):
    """
    جلب معلومات المنصات المرتبطة بالحساب
    """
    result = {
        "success": False,
        "bounded_accounts": [],
        "available_platforms": [],
        "error": None
    }
    
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        headers = {
            "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            result["error"] = f"Failed to fetch data (HTTP {response.status_code})"
            return JSONResponse(result)
        
        data = response.json()
        
        bounded_accounts = data.get("bounded_accounts", [])
        available_platforms = data.get("available_platforms", [])
        
        for p_id in bounded_accounts:
            result["bounded_accounts"].append({
                "id": p_id,
                "name": PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
            })
        
        for p_id in available_platforms:
            result["available_platforms"].append({
                "id": p_id,
                "name": PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
            })
        
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 10. ACCESS TOKEN TO JWT
# ============================================================
@app.post("/api/token-to-jwt")
async def api_token_to_jwt(access_token: str = Form(...)):
    """
    تحويل Access Token إلى JWT
    """
    result = {
        "success": False,
        "jwt_token": None,
        "player": {},
        "credits": {},
        "error": None
    }
    
    try:
        url = f"https://jwt-system-ff.vercel.app/access_to_jwt?access_token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                result["success"] = True
                result["jwt_token"] = data.get("jwt_token")
                result["player"] = {
                    "uid": data.get("uid"),
                    "nickname": data.get("nickname"),
                    "region": data.get("lock_region"),
                    "platform": data.get("platform_name"),
                    "open_id": data.get("open_id")
                }
                result["credits"] = data.get("credits", {})
            else:
                result["error"] = "API returned success=False"
        else:
            result["error"] = f"Server Error! HTTP Status Code: {response.status_code}"
            
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 11. ACCESS TOKEN TO BAN
# ============================================================
@app.post("/api/ban-account")
async def api_ban_account(access_token: str = Form(...)):
    """
    حظر الحساب (تحذير: استخدام بحذر)
    """
    result = {
        "success": False,
        "response": None,
        "error": None
    }
    
    try:
        url = f"https://toji-api-jwt.vercel.app/ban?token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        result["response"] = {
            "status_code": response.status_code,
            "text": response.text
        }
        
        if response.status_code == 200:
            try:
                result["response"]["json"] = response.json()
                result["success"] = True
            except:
                result["success"] = True
        else:
            result["error"] = f"HTTP {response.status_code}"
            
    except Exception as e:
        result["error"] = str(e)
    
    return JSONResponse(result)


# ============================================================
# 12. OWNER DETAILS (Info فقط)
# ============================================================
@app.get("/api/owner")
async def api_owner():
    """
    معلومات المطور
    """
    return JSONResponse({
        "developer": "—͞𝑨𝑩𝑫𝑶𝑿",
        "telegram": "@FF720H",
        "version": "v3.0 (Premium AbdoX Edition)",
        "note": "Thank you for using AbdoX Bind Tool!"
    })
    
    