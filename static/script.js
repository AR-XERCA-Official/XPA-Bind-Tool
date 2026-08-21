// ============================================================
// DROGON BIND TOOL - WEB EDITION
// Frontend JavaScript - Black & Red Theme
// ============================================================

// ============================================================
// GLOBAL STATE
// ============================================================
let currentAction = null;
let currentStep = 0;
let stepData = {};

// ============================================================
// DOM REFS
// ============================================================
const tokenInput = document.getElementById('accessToken');
const outputContent = document.getElementById('outputContent');
const inputSection = document.getElementById('inputSection');
const inputContent = document.getElementById('inputContent');

// ============================================================
// HELPER FUNCTIONS
// ============================================================
function getToken() {
    return tokenInput.value.trim();
}

function setToken(val) {
    tokenInput.value = val;
}

function clearToken() {
    tokenInput.value = '';
    tokenInput.focus();
}

function clearOutput() {
    outputContent.innerHTML = `
        <div class="output-placeholder">
            <span class="dim">┌─────────────────────────────────────────┐</span><br>
            <span class="dim">│  Output cleared.                        │</span><br>
            <span class="dim">│  Ready for next command...              │</span><br>
            <span class="dim">└─────────────────────────────────────────┘</span>
        </div>
    `;
}

function appendOutput(text, type = 'info') {
    const colorMap = {
        'success': 'success',
        'error': 'error',
        'info': 'info',
        'gold': 'gold',
        'red': 'red',
        'green': 'green',
        'cyan': 'cyan',
        'yellow': 'yellow',
        'magenta': 'magenta',
        'dim': 'dim',
        'white': 'white',
        'bold': 'bold'
    };
    
    const cls = colorMap[type] || 'white';
    const lines = text.split('\n');
    const wrapped = lines.map(line => {
        // تطبيق الألوان على النصوص المحددة
        let formatted = line
            .replace(/✓/g, '<span class="success">✓</span>')
            .replace(/✗/g, '<span class="error">✗</span>')
            .replace(/ℹ/g, '<span class="info">ℹ</span>')
            .replace(/▶/g, '<span class="gold">▶</span>')
            .replace(/●/g, '<span class="gold">●</span>')
            .replace(/🐉/g, '<span class="red">🐉</span>')
            .replace(/╔/g, '<span class="dim">╔</span>')
            .replace(/╗/g, '<span class="dim">╗</span>')
            .replace(/╚/g, '<span class="dim">╚</span>')
            .replace(/╝/g, '<span class="dim">╝</span>')
            .replace(/═/g, '<span class="dim">═</span>')
            .replace(/║/g, '<span class="dim">║</span>')
            .replace(/╠/g, '<span class="dim">╠</span>')
            .replace(/╣/g, '<span class="dim">╣</span>');
        return `<span class="${cls}">${formatted}</span>`;
    });
    
    // إزالة placeholder إذا موجود
    const placeholder = outputContent.querySelector('.output-placeholder');
    if (placeholder) {
        outputContent.innerHTML = '';
    }
    
    outputContent.innerHTML += wrapped.join('\n') + '\n';
    outputContent.scrollTop = outputContent.scrollHeight;
}

function showLoading() {
    appendOutput('⏳ Processing... Please wait.', 'info');
}

function hideInputSection() {
    inputSection.style.display = 'none';
    inputContent.innerHTML = '';
    currentAction = null;
    currentStep = 0;
    stepData = {};
}

function showInput(action) {
    currentAction = action;
    currentStep = 0;
    stepData = {};
    inputSection.style.display = 'block';
    
    const templates = {
        'bind-email': `
            <label>📧 BIND EMAIL</label>
            <div class="input-hint">Step 1: Send OTP to email</div>
            <input type="email" id="bindEmail" placeholder="Enter email to bind">
            <button class="btn-submit" onclick="bindEmailStep1()">📨 Send OTP</button>
            <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
        `,
        'unbind-email': `
            <label>🔓 UNBIND EMAIL</label>
            <div class="input-hint">Choose method:</div>
            <button class="btn-submit" onclick="unbindEmail('otp')" style="margin:5px;">🔑 Via OTP</button>
            <button class="btn-submit" onclick="unbindEmail('code')" style="margin:5px;background:#880000;">🔐 Via Security Code</button>
            <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
        `,
        'change-bind': `
            <label>🔄 CHANGE BIND EMAIL</label>
            <div class="input-hint">Choose method:</div>
            <button class="btn-submit" onclick="changeBind('otp')" style="margin:5px;">🔑 Via OTP</button>
            <button class="btn-submit" onclick="changeBind('code')" style="margin:5px;background:#880000;">🔐 Via Security Code</button>
            <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
        `,
        'eat-to-token': `
            <label>🍽️ EAT TO ACCESS TOKEN</label>
            <div class="input-hint">Paste EAT token or full URL containing eat=</div>
            <input type="text" id="eatInput" placeholder="EAT token or URL">
            <button class="btn-submit" onclick="eatToToken()">⚡ Convert</button>
            <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
        `,
        'login-history': `
            <label>📜 LOGIN HISTORY</label>
            <div class="input-hint">Enter Access Token or JWT</div>
            <input type="text" id="historyToken" placeholder="Access Token or JWT">
            <button class="btn-submit" onclick="loginHistory()">📊 Fetch History</button>
            <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
        `
    };
    
    inputContent.innerHTML = templates[action] || `<div class="error">Unknown action</div>`;
}

// ============================================================
// BIND EMAIL - Multi-step
// ============================================================
let bindEmailData = {};

function bindEmailStep1() {
    const email = document.getElementById('bindEmail').value.trim();
    if (!email) {
        appendOutput('✗ Please enter an email address.', 'error');
        return;
    }
    
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token first.', 'error');
        return;
    }
    
    bindEmailData.email = email;
    showLoading();
    
    fetch('/api/bind-email/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token, email: email })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ OTP sent successfully to ' + email, 'success');
            showBindEmailStep2();
        } else {
            appendOutput('✗ Failed to send OTP: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showBindEmailStep2() {
    inputContent.innerHTML = `
        <label>📧 BIND EMAIL - Step 2</label>
        <div class="input-hint">Enter OTP received at ${bindEmailData.email}</div>
        <input type="text" id="bindOtp" placeholder="Enter OTP code">
        <button class="btn-submit" onclick="bindEmailStep2()">✅ Verify OTP</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function bindEmailStep2() {
    const otp = document.getElementById('bindOtp').value.trim();
    if (!otp) {
        appendOutput('✗ Please enter OTP.', 'error');
        return;
    }
    
    const token = getToken();
    if (!token) {
        appendOutput('✗ Token missing.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/bind-email/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: bindEmailData.email,
            otp: otp
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.verifier_token) {
            bindEmailData.verifier_token = data.verifier_token;
            appendOutput('✓ OTP verified!', 'success');
            showBindEmailStep3();
        } else {
            appendOutput('✗ OTP verification failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showBindEmailStep3() {
    inputContent.innerHTML = `
        <label>📧 BIND EMAIL - Step 3</label>
        <div class="input-hint">Set 6-digit security code</div>
        <input type="password" id="bindSecurityCode" placeholder="6-digit security code" maxlength="6">
        <button class="btn-submit" onclick="bindEmailStep3()">🔒 Finalize Bind</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function bindEmailStep3() {
    const securityCode = document.getElementById('bindSecurityCode').value.trim();
    if (!securityCode || securityCode.length < 6) {
        appendOutput('✗ Please enter a 6-digit security code.', 'error');
        return;
    }
    
    const token = getToken();
    if (!token) {
        appendOutput('✗ Token missing.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/bind-email/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: bindEmailData.email,
            verifier_token: bindEmailData.verifier_token,
            security_code: securityCode
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ Email bound successfully!', 'success');
            appendOutput('📧 ' + bindEmailData.email + ' is now linked.', 'gold');
            hideInputSection();
        } else {
            appendOutput('✗ Bind failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// UNBIND EMAIL
// ============================================================
function unbindEmail(method) {
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token first.', 'error');
        return;
    }
    
    // جلب الإيميل المرتبط
    showLoading();
    fetch('/api/unbind-email/get-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.email) {
            appendOutput('✓ Found bound email: ' + data.email, 'success');
            if (method === 'otp') {
                showUnbindOTPStep(data.email);
            } else {
                showUnbindCodeStep(data.email);
            }
        } else {
            appendOutput('✗ ' + (data.message || 'No email found to unbind'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showUnbindOTPStep(email) {
    inputContent.innerHTML = `
        <label>🔓 UNBIND EMAIL - Via OTP</label>
        <div class="input-hint">Sending OTP to ${email}...</div>
        <input type="text" id="unbindOtp" placeholder="Enter OTP from email">
        <button class="btn-submit" onclick="unbindOTPVerify('${email}')">✅ Verify OTP</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
    
    // إرسال OTP تلقائياً
    const token = getToken();
    fetch('/api/unbind-email/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token, email: email })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ OTP sent to ' + email, 'success');
        } else {
            appendOutput('✗ Failed to send OTP: ' + (data.message || 'Unknown error'), 'error');
        }
    });
}

function unbindOTPVerify(email) {
    const otp = document.getElementById('unbindOtp').value.trim();
    if (!otp) {
        appendOutput('✗ Please enter OTP.', 'error');
        return;
    }
    
    const token = getToken();
    showLoading();
    
    fetch('/api/unbind-email/verify-identity-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: email,
            otp: otp
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.identity_token) {
            appendOutput('✓ Identity verified!', 'success');
            finalizeUnbind(data.identity_token);
        } else {
            appendOutput('✗ Verification failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showUnbindCodeStep(email) {
    inputContent.innerHTML = `
        <label>🔓 UNBIND EMAIL - Via Security Code</label>
        <div class="input-hint">Enter your 6-digit security code</div>
        <input type="password" id="unbindCode" placeholder="6-digit security code" maxlength="6">
        <button class="btn-submit" onclick="unbindCodeVerify('${email}')">🔐 Verify Code</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function unbindCodeVerify(email) {
    const code = document.getElementById('unbindCode').value.trim();
    if (!code || code.length < 6) {
        appendOutput('✗ Please enter a 6-digit security code.', 'error');
        return;
    }
    
    const token = getToken();
    showLoading();
    
    fetch('/api/unbind-email/verify-identity-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: email,
            security_code: code
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.identity_token) {
            appendOutput('✓ Identity verified!', 'success');
            finalizeUnbind(data.identity_token);
        } else {
            appendOutput('✗ Verification failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function finalizeUnbind(identityToken) {
    const token = getToken();
    showLoading();
    
    fetch('/api/unbind-email/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            identity_token: identityToken
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ Email unbound successfully!', 'success');
            hideInputSection();
        } else {
            appendOutput('✗ Unbind failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// CHANGE BIND
// ============================================================
let changeData = {};

function changeBind(method) {
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token first.', 'error');
        return;
    }
    
    showLoading();
    fetch('/api/change-bind/get-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.email) {
            changeData.oldEmail = data.email;
            appendOutput('✓ Current email: ' + data.email, 'success');
            if (method === 'otp') {
                showChangeOTPStep();
            } else {
                showChangeCodeStep();
            }
        } else {
            appendOutput('✗ ' + (data.message || 'No email found'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showChangeOTPStep() {
    inputContent.innerHTML = `
        <label>🔄 CHANGE BIND - Via OTP</label>
        <div class="input-hint">Enter OTP from ${changeData.oldEmail}</div>
        <input type="text" id="changeOtp" placeholder="Enter OTP">
        <button class="btn-submit" onclick="changeOTPVerify()">✅ Verify OTP</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
    
    const token = getToken();
    fetch('/api/change-bind/send-otp-old', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: changeData.oldEmail
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ OTP sent to ' + changeData.oldEmail, 'success');
        } else {
            appendOutput('✗ Failed: ' + (data.message || 'Unknown'), 'error');
        }
    });
}

function changeOTPVerify() {
    const otp = document.getElementById('changeOtp').value.trim();
    if (!otp) {
        appendOutput('✗ Please enter OTP.', 'error');
        return;
    }
    
    const token = getToken();
    showLoading();
    
    fetch('/api/change-bind/verify-identity-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: changeData.oldEmail,
            otp: otp
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.identity_token) {
            changeData.identityToken = data.identity_token;
            appendOutput('✓ Identity verified!', 'success');
            showChangeNewEmailStep();
        } else {
            appendOutput('✗ Verification failed: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showChangeCodeStep() {
    inputContent.innerHTML = `
        <label>🔄 CHANGE BIND - Via Security Code</label>
        <div class="input-hint">Enter your 6-digit security code</div>
        <input type="password" id="changeCode" placeholder="6-digit code" maxlength="6">
        <button class="btn-submit" onclick="changeCodeVerify()">🔐 Verify Code</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function changeCodeVerify() {
    const code = document.getElementById('changeCode').value.trim();
    if (!code || code.length < 6) {
        appendOutput('✗ Please enter 6-digit security code.', 'error');
        return;
    }
    
    const token = getToken();
    showLoading();
    
    fetch('/api/change-bind/verify-identity-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            email: changeData.oldEmail,
            security_code: code
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.identity_token) {
            changeData.identityToken = data.identity_token;
            appendOutput('✓ Identity verified!', 'success');
            showChangeNewEmailStep();
        } else {
            appendOutput('✗ Verification failed: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showChangeNewEmailStep() {
    inputContent.innerHTML = `
        <label>🔄 CHANGE BIND - New Email</label>
        <div class="input-hint">Enter new email address</div>
        <input type="email" id="changeNewEmail" placeholder="new@email.com">
        <button class="btn-submit" onclick="changeSendNewOTP()">📨 Send OTP to new email</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function changeSendNewOTP() {
    const newEmail = document.getElementById('changeNewEmail').value.trim();
    if (!newEmail) {
        appendOutput('✗ Please enter new email.', 'error');
        return;
    }
    
    changeData.newEmail = newEmail;
    const token = getToken();
    showLoading();
    
    fetch('/api/change-bind/send-otp-new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            new_email: newEmail
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ OTP sent to ' + newEmail, 'success');
            showChangeVerifyNewOTPStep();
        } else {
            appendOutput('✗ Failed: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function showChangeVerifyNewOTPStep() {
    inputContent.innerHTML = `
        <label>🔄 CHANGE BIND - Verify New Email</label>
        <div class="input-hint">Enter OTP from ${changeData.newEmail}</div>
        <input type="text" id="changeNewOtp" placeholder="Enter OTP">
        <button class="btn-submit" onclick="changeVerifyNewOTP()">✅ Verify OTP</button>
        <button class="btn-cancel" onclick="hideInputSection()">Cancel</button>
    `;
}

function changeVerifyNewOTP() {
    const otp = document.getElementById('changeNewOtp').value.trim();
    if (!otp) {
        appendOutput('✗ Please enter OTP.', 'error');
        return;
    }
    
    const token = getToken();
    showLoading();
    
    fetch('/api/change-bind/verify-otp-new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            new_email: changeData.newEmail,
            otp: otp
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success' && data.verifier_token) {
            changeData.verifierToken = data.verifier_token;
            appendOutput('✓ OTP verified!', 'success');
            finalizeChange();
        } else {
            appendOutput('✗ Verification failed: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

function finalizeChange() {
    const token = getToken();
    showLoading();
    
    fetch('/api/change-bind/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            access_token: token,
            identity_token: changeData.identityToken,
            new_email: changeData.newEmail,
            verifier_token: changeData.verifierToken
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            appendOutput('✓ Email changed successfully!', 'success');
            appendOutput('📧 ' + changeData.oldEmail + ' → ' + changeData.newEmail, 'gold');
            hideInputSection();
        } else {
            appendOutput('✗ Change failed: ' + (data.message || 'Unknown'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// EXECUTE SIMPLE ACTIONS
// ============================================================
function executeAction(action) {
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token first.', 'error');
        return;
    }
    
    showLoading();
    
    const endpoints = {
        'cancel-bind': '/api/cancel-bind',
        'revoke-token': '/api/revoke-token',
        'token-to-jwt': '/api/token-to-jwt',
        'ban-account': '/api/ban-account'
    };
    
    const endpoint = endpoints[action];
    if (!endpoint) {
        appendOutput('✗ Unknown action.', 'error');
        return;
    }
    
    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success || data.status === 'success') {
            appendOutput('✓ ' + action.replace('-', ' ').toUpperCase() + ' completed!', 'success');
            // عرض البيانات
            if (data.player) {
                appendOutput('  🐉 Player: ' + (data.player.nickname || 'N/A'), 'info');
                appendOutput('  📊 UID: ' + (data.player.account_id || data.player.uid || 'N/A'), 'info');
            }
            if (data.jwt_token) {
                appendOutput('  🔑 JWT: ' + data.jwt_token.substring(0, 40) + '...', 'gold');
            }
            if (data.bounded_accounts) {
                appendOutput('  🔗 Bound Platforms:', 'info');
                data.bounded_accounts.forEach(p => {
                    appendOutput('    ● ' + p.name, 'dim');
                });
            }
            if (data.history) {
                appendOutput('  📜 Login History (' + data.history.length + ' records):', 'info');
                data.history.forEach((h, i) => {
                    appendOutput('    ' + (i+1) + '. ' + h.date + ' | ' + h.device, 'dim');
                });
            }
            if (data.response) {
                appendOutput('  📦 Response: ' + JSON.stringify(data.response, null, 2), 'dim');
            }
            if (action === 'revoke-token' && data.success) {
                appendOutput('  ✅ Token revoked successfully!', 'success');
            }
            if (action === 'ban-account') {
                appendOutput('  ⚠️ Ban request sent! Check response above.', 'red');
            }
        } else {
            appendOutput('✗ Failed: ' + (data.error || data.message || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// EAT TO TOKEN
// ============================================================
function eatToToken() {
    const eatInput = document.getElementById('eatInput').value.trim();
    if (!eatInput) {
        appendOutput('✗ Please enter EAT token or URL.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/eat-to-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ eat_input: eatInput })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.access_token) {
            appendOutput('✓ EAT converted successfully!', 'success');
            appendOutput('  🐉 Nickname: ' + (data.player?.nickname || 'N/A'), 'info');
            appendOutput('  📊 UID: ' + (data.player?.account_id || 'N/A'), 'info');
            appendOutput('  🌍 Region: ' + (data.player?.region || 'N/A'), 'info');
            appendOutput('  🔑 Access Token:', 'gold');
            appendOutput('  ' + data.access_token, 'white');
            // Auto-fill token
            setToken(data.access_token);
            appendOutput('  ✅ Token auto-filled!', 'success');
            hideInputSection();
        } else {
            appendOutput('✗ Failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// LOGIN HISTORY
// ============================================================
function loginHistory() {
    const tokenInput = document.getElementById('historyToken');
    const token = tokenInput ? tokenInput.value.trim() : getToken();
    
    if (!token) {
        appendOutput('✗ Please enter token.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/login-history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            appendOutput('✓ Login history fetched!', 'success');
            if (data.player) {
                appendOutput('  🐉 Player: ' + (data.player.nickname || 'N/A'), 'info');
                appendOutput('  📊 UID: ' + (data.player.account_id || 'N/A'), 'info');
            }
            if (data.history && data.history.length > 0) {
                appendOutput('  📜 ' + data.history.length + ' login records:', 'gold');
                data.history.forEach((h, i) => {
                    appendOutput('    ' + (i+1) + '. ' + h.date + ' | ' + h.device + ' | RAM: ' + h.ram + 'MB', 'dim');
                });
            } else {
                appendOutput('  ℹ No login history found.', 'info');
            }
            hideInputSection();
        } else {
            appendOutput('✗ Failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// FETCH BIND INFO (Quick Action)
// ============================================================
function fetchBindInfo() {
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/bind-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            appendOutput('✓ Bind Info fetched!', 'success');
            if (data.player) {
                appendOutput('  🐉 Nickname: ' + (data.player.nickname || 'N/A'), 'info');
                appendOutput('  📊 UID: ' + (data.player.uid || 'N/A'), 'info');
                appendOutput('  🌍 Region: ' + (data.player.region || 'N/A'), 'info');
            }
            if (data.bind) {
                appendOutput('  📧 Email: ' + (data.bind.email || 'None'), 'info');
                appendOutput('  ⏳ Pending: ' + (data.bind.email_to_be || 'None'), 'info');
                if (data.bind.summary) {
                    appendOutput('  📝 Summary: ' + data.bind.summary, 'gold');
                }
            }
        } else {
            appendOutput('✗ Failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// FETCH BOUND ACCOUNTS (Quick Action)
// ============================================================
function fetchBoundAccounts() {
    const token = getToken();
    if (!token) {
        appendOutput('✗ Please enter Access Token.', 'error');
        return;
    }
    
    showLoading();
    
    fetch('/api/bound-accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ access_token: token })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            appendOutput('✓ Bound accounts fetched!', 'success');
            if (data.bounded_accounts && data.bounded_accounts.length > 0) {
                appendOutput('  🔗 Bound Platforms:', 'gold');
                data.bounded_accounts.forEach(p => {
                    appendOutput('    ● ' + p.name, 'dim');
                });
            } else {
                appendOutput('  ℹ No third-party platforms bound.', 'info');
            }
            if (data.available_platforms && data.available_platforms.length > 0) {
                appendOutput('  📋 Available to bind:', 'info');
                data.available_platforms.forEach(p => {
                    appendOutput('    ● ' + p.name, 'dim');
                });
            }
        } else {
            appendOutput('✗ Failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(err => {
        appendOutput('✗ Error: ' + err.message, 'error');
    });
}

// ============================================================
// OWNER DETAILS
// ============================================================
function showOwnerDetails() {
    appendOutput('🐉 —͞𝑨𝑩𝑫𝑶𝑿 𝑩𝑰𝑵𝑫 𝑻𝑶𝑶𝑳 v3.0', 'gold');
    appendOutput('═══════════════════════════════════', 'dim');
    
    fetch('/api/owner')
        .then(r => r.json())
        .then(data => {
            appendOutput('  👨‍💻 Developer: ' + data.developer, 'red');
            appendOutput('  📱 Telegram: ' + data.telegram, 'info');
            appendOutput('  📢 Channel: ' + data.channel, 'info');
            appendOutput('  📦 Version: ' + data.version, 'gold');
            appendOutput('  🔥 ' + data.note, 'green');
            appendOutput('═══════════════════════════════════', 'dim');
        })
        .catch(err => {
            appendOutput('✗ Error fetching owner details: ' + err.message, 'error');
        });
}

// ============================================================
// KEYBOARD SHORTCUTS
// ============================================================
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to execute current action
    if (e.ctrlKey && e.key === 'Enter') {
        const activeBtn = document.querySelector('.btn-submit:focus');
        if (activeBtn) {
            activeBtn.click();
        }
    }
    // Escape to close input section
    if (e.key === 'Escape') {
        hideInputSection();
    }
});

// Enter key on token input to focus first action
tokenInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const firstAction = document.querySelector('.btn-action');
        if (firstAction) {
            firstAction.click();
        }
    }
});

// Auto-focus token input on load
window.addEventListener('load', function() {
    tokenInput.focus();
    appendOutput(' —͞𝑨𝑩𝑫𝑶𝑿 𝑩𝑰𝑵𝑫 𝑻𝑶𝑶𝑳 v3.0 loaded.', 'gold');
    appendOutput('📌 Enter Access Token and select an action.', 'info');
    appendOutput('💡 Tip: Use Ctrl+Enter to submit forms.', 'dim');
});