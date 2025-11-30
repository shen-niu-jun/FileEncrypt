// 使用URL方式下载文件的版本
console.log("文件加密工具 - JavaScript加载成功 (URL模式)");

// 全局变量
let selectedFile = null;

// 后端API配置
const API_CONFIG = {
    baseUrl: 'http://localhost:5000',
    endpoints: {
        health: '/api/health',
        test: '/api/test',
        processFile: '/api/process-file',
        download: '/api/download',
        fileInfo: '/api/file-info'
    }
};

// 初始化函数
function init() {
    console.log("开始初始化...");
    
    // 绑定事件监听器
    setupEventListeners();
    
    // 检查后端连接状态
    checkBackendStatus();
    
    console.log("初始化完成");
}

// 设置事件监听器
function setupEventListeners() {
    const fileInput = document.getElementById('fileInput');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const dropZone = document.getElementById('dropZone');
    const encryptBtn = document.getElementById('encryptBtn');
    const decryptBtn = document.getElementById('decryptBtn');
    
    console.log("设置事件监听器...");
    
    // 文件选择按钮点击事件
    if (selectFileBtn && fileInput) {
        selectFileBtn.addEventListener('click', function() {
            console.log("触发文件选择");
            fileInput.click();
        });
    }
    
    // 文件选择变化事件
    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                setSelectedFile(file);
            }
        });
    }
    
    // 拖放事件
    if (dropZone) {
        dropZone.addEventListener('dragover', function(event) {
            event.preventDefault();
            this.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', function(event) {
            event.preventDefault();
            this.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', function(event) {
            event.preventDefault();
            this.classList.remove('dragover');
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                setSelectedFile(files[0]);
            }
        });
    }
    
    // 加密解密按钮
    if (encryptBtn) {
        encryptBtn.addEventListener('click', function() {
            console.log("加密按钮点击");
            processFile('encrypt');
        });
    }
    
    if (decryptBtn) {
        decryptBtn.addEventListener('click', function() {
            console.log("解密按钮点击");
            processFile('decrypt');
        });
    }
}

// 检查后端状态
async function checkBackendStatus() {
    try {
        const url = API_CONFIG.baseUrl + API_CONFIG.endpoints.health;
        console.log("检查后端状态:", url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log("健康检查响应状态:", response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✓ 后端服务连接正常:', data.message);
            showStatus('后端服务已连接', 'success');
        } else {
            const errorText = await response.text();
            console.error('后端响应异常:', response.status, errorText);
            showStatus(`后端服务异常: ${response.status}`, 'error');
        }
    } catch (error) {
        console.error('后端连接失败:', error);
        showStatus('无法连接到后端服务，请确保Python服务已启动在 localhost:5000', 'error');
    }
}

// 设置选中的文件
function setSelectedFile(file) {
    selectedFile = file;
    
    // 更新UI显示文件信息
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileInfo = document.getElementById('fileInfo');
    const decryptBtn = document.getElementById('decryptBtn');
    
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (fileInfo) fileInfo.style.display = 'block';
    
    // 根据文件扩展名启用/禁用解密按钮
    if (decryptBtn) {
        const isEncrypted = file.name.endsWith('.encrypted');
        decryptBtn.disabled = !isEncrypted;
        if (!isEncrypted) {
            decryptBtn.title = "只有加密后的文件(.encrypted)才能解密";
        } else {
            decryptBtn.title = "";
        }
    }
    
    console.log("文件已选择:", file.name);
    showStatus(`已选择文件: ${file.name}`, 'info');
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 处理文件（加密/解密）
async function processFile(action) {
    console.log(`开始处理文件，动作: ${action}`);
    
    // 基本验证
    if (!selectedFile) {
        showStatus('请先选择文件', 'error');
        return;
    }
    
    const passwordInput = document.getElementById('passwordInput');
    if (!passwordInput || !passwordInput.value) {
        showStatus('请输入密码', 'error');
        return;
    }
    
    const password = passwordInput.value;
    
    // 禁用按钮，防止重复点击
    setButtonsEnabled(false);
    showStatus(`正在${action === 'encrypt' ? '加密' : '解密'}文件...`, 'info');
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('password', password);
        formData.append('action', action);
        
        const url = API_CONFIG.baseUrl + API_CONFIG.endpoints.processFile;
        console.log("发送请求到:", url);
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        console.log("响应状态:", response.status);
        
        const result = await response.json();
        console.log("处理结果:", result);
        
        if (result.success) {
            showStatus(`文件${action === 'encrypt' ? '加密' : '解密'}成功！准备下载...`, 'success');
            
            // 使用URL方式下载文件
            const downloadUrl = API_CONFIG.baseUrl + result.download_url;
            console.log("下载URL:", downloadUrl);
            
            // 方法1: 直接跳转（最简单可靠）
            showStatus(`文件已准备好，<a href="${downloadUrl}" download="${result.filename}" style="color: blue; text-decoration: underline; font-weight: bold;">点击这里下载文件</a>`, 'success');
            
            // 方法2: 自动下载（可能被浏览器阻止）
            // setTimeout(() => {
            //     window.location.href = downloadUrl;
            // }, 1000);
            
            // 清空选择，准备下一次操作
            resetFileSelection();
            if (passwordInput) passwordInput.value = '';
        } else {
            showStatus(result.error || '处理失败', 'error');
        }
        
    } catch (error) {
        console.error('请求失败:', error);
        showStatus(`请求失败: ${error.message}`, 'error');
    } finally {
        setButtonsEnabled(true);
    }
}

// 重置文件选择
function resetFileSelection() {
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    
    if (fileInput) fileInput.value = '';
    if (fileInfo) fileInfo.style.display = 'none';
    
    selectedFile = null;
}

// 显示状态消息
function showStatus(message, type) {
    const statusElement = document.getElementById('statusMessage');
    if (statusElement) {
        statusElement.innerHTML = message; // 使用innerHTML以支持链接
        statusElement.className = `status-message ${type}`;
    } else {
        // 备用方案：使用alert
        alert(`${type.toUpperCase()}: ${message.replace(/<[^>]*>/g, '')}`);
    }
}

// 启用/禁用按钮
function setButtonsEnabled(enabled) {
    const encryptBtn = document.getElementById('encryptBtn');
    const decryptBtn = document.getElementById('decryptBtn');
    
    if (encryptBtn) encryptBtn.disabled = !enabled;
    if (decryptBtn) decryptBtn.disabled = !enabled;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);