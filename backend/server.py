from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import tempfile
import traceback
import shutil
import uuid
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# 允许所有源的CORS
CORS(app)

# 手动添加CORS头
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 创建文件存储目录
FILES_DIR = "processed_files"
os.makedirs(FILES_DIR, exist_ok=True)

# 存储文件信息的字典（在生产环境中应该使用数据库）
file_registry = {}

# 导入加密器
try:
    from encryptor_wrapper import EncryptorWrapper
    
    print("初始化加密器...")
    encryptor = EncryptorWrapper()
    print("✓ 加密器初始化成功")
        
except Exception as e:
    print(f"加密器初始化失败: {e}")
    traceback.print_exc()
    encryptor = None

# 文件清理函数（定期清理旧文件）
def cleanup_old_files():
    """定期清理超过1小时的旧文件"""
    while True:
        try:
            current_time = datetime.now()
            files_to_delete = []
            
            # 找出需要删除的文件
            for file_id, file_info in list(file_registry.items()):
                if current_time - file_info['created_time'] > timedelta(hours=1):
                    files_to_delete.append(file_id)
            
            # 删除文件和注册信息
            for file_id in files_to_delete:
                file_path = file_registry[file_id]['file_path']
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"清理旧文件: {file_path}")
                    except Exception as e:
                        print(f"清理文件失败 {file_path}: {e}")
                del file_registry[file_id]
            
            # 每10分钟运行一次
            time.sleep(600)
            
        except Exception as e:
            print(f"文件清理错误: {e}")
            time.sleep(60)

# 启动文件清理线程
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def home():
    return jsonify({
        "message": "文件加密服务运行中",
        "status": "ok",
        "version": "2.0 - URL模式",
        "endpoints": {
            "health": "/api/health",
            "test": "/api/test", 
            "process_file": "/api/process-file"
        }
    })

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """健康检查接口"""
    if encryptor is None:
        return jsonify({"status": "error", "message": "加密器未初始化"}), 500
    return jsonify({"status": "ok", "message": "服务运行正常"})

@app.route('/api/test', methods=['GET', 'OPTIONS'])
def test_connection():
    """测试连接和DLL功能"""
    try:
        if encryptor is None:
            return jsonify({"error": "加密器未初始化"}), 500
            
        # 创建一个测试文件来验证DLL工作
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            encrypted_file = os.path.join(temp_dir, "test_encrypted.txt")
            decrypted_file = os.path.join(temp_dir, "test_decrypted.txt")
            
            # 创建测试内容
            test_content = "Hello, this is a test from the server!"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            print("测试加密...")
            # 测试加密
            encrypt_result = encryptor.process_file(test_file, encrypted_file, "testpassword")
            print(f"加密结果: {encrypt_result}")
            
            decrypt_result = False
            if encrypt_result and os.path.exists(encrypted_file):
                print("测试解密...")
                # 测试解密
                decrypt_result = encryptor.process_file(encrypted_file, decrypted_file, "testpassword")
                print(f"解密结果: {decrypt_result}")
            
            return jsonify({
                "dll_working": encrypt_result and decrypt_result,
                "encrypt_success": encrypt_result,
                "decrypt_success": decrypt_result,
                "message": "DLL测试完成",
                "test_content": test_content
            })
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()
        return jsonify({"error": f"测试失败: {str(e)}"}), 500

@app.route('/api/process-file', methods=['POST', 'OPTIONS'])
def process_file():
    """主要的文件处理接口 - URL版本"""
    try:
        print("=== 收到文件处理请求 ===")
        
        if encryptor is None:
            return jsonify({"error": "加密器未初始化"}), 500
        
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        action = request.form.get('action', 'encrypt')
        
        print(f"文件名: {file.filename}")
        print(f"动作: {action}")
        print(f"密码长度: {len(password)}")
        
        if not file or not file.filename:
            return jsonify({"error": "没有选择文件"}), 400
        
        if not password:
            return jsonify({"error": "密码不能为空"}), 400
        
        # 创建唯一文件名
        file_id = str(uuid.uuid4())
        
        if action == 'encrypt':
            output_filename = f"{file.filename}.encrypted"
        else:
            # 解密时，移除.encrypted后缀
            if file.filename.endswith('.encrypted'):
                output_filename = file.filename[:-10]  # 移除.encrypted
            else:
                output_filename = f"{file.filename}.decrypted"
        
        # 保存输入文件
        input_path = os.path.join(FILES_DIR, f"{file_id}_input")
        file.save(input_path)
        
        if not os.path.exists(input_path):
            return jsonify({"error": "文件保存失败"}), 500
        
        input_size = os.path.getsize(input_path)
        print(f"输入文件保存成功，大小: {input_size} 字节")
        
        # 处理文件
        output_path = os.path.join(FILES_DIR, f"{file_id}_{output_filename}")
        print(f"输出路径: {output_path}")
        
        result = encryptor.process_file(input_path, output_path, password)
        print(f"处理结果: {result}")
        
        # 清理输入文件
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if result and os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"处理成功，输出文件大小: {output_size} 字节")
            
            # 注册文件信息
            file_registry[file_id] = {
                'file_path': output_path,
                'original_name': output_filename,
                'created_time': datetime.now()
            }
            
            # 返回下载URL
            download_url = f"/api/download/{file_id}"
            
            return jsonify({
                "success": True,
                "message": f"文件{action}成功",
                "download_url": download_url,
                "filename": output_filename,
                "file_size": output_size,
                "file_id": file_id
            })
        else:
            error_msg = "文件处理失败"
            print(f"处理失败: {error_msg}")
            return jsonify({"error": error_msg}), 500
                
    except Exception as e:
        print("处理文件时发生错误:")
        traceback.print_exc()
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """提供文件下载"""
    try:
        if file_id not in file_registry:
            return jsonify({"error": "文件不存在或已过期"}), 404
        
        file_info = file_registry[file_id]
        file_path = file_info['file_path']
        original_name = file_info['original_name']
        
        if not os.path.exists(file_path):
            # 文件不存在，清理注册信息
            del file_registry[file_id]
            return jsonify({"error": "文件不存在"}), 404
        
        print(f"提供文件下载: {original_name} -> {file_path}")
        
        # 发送文件
        return send_file(
            file_path,
            as_attachment=True,
            download_name=original_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        print(f"文件下载错误: {e}")
        return jsonify({"error": f"下载失败: {str(e)}"}), 500

@app.route('/api/file-info/<file_id>', methods=['GET'])
def get_file_info(file_id):
    """获取文件信息"""
    if file_id not in file_registry:
        return jsonify({"error": "文件不存在或已过期"}), 404
    
    file_info = file_registry[file_id]
    return jsonify({
        "filename": file_info['original_name'],
        "created_time": file_info['created_time'].isoformat(),
        "file_exists": os.path.exists(file_info['file_path'])
    })

@app.route('/api/cleanup', methods=['POST'])
def manual_cleanup():
    """手动清理所有文件（用于调试）"""
    try:
        count = 0
        for file_id, file_info in list(file_registry.items()):
            file_path = file_info['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
                count += 1
        file_registry.clear()
        return jsonify({"message": f"清理了 {count} 个文件"})
    except Exception as e:
        return jsonify({"error": f"清理失败: {str(e)}"}), 500

if __name__ == '__main__':
    print("启动文件加密服务 (URL模式)...")
    print("可用端点:")
    print("  GET  /api/health          - 健康检查")
    print("  GET  /api/test            - DLL功能测试") 
    print("  POST /api/process-file    - 文件处理")
    print("  GET  /api/download/<id>   - 下载文件")
    print("  GET  /api/file-info/<id>  - 文件信息")
    print("  POST /api/cleanup         - 手动清理")
    app.run(host='127.0.0.1', port=5000, debug=True)