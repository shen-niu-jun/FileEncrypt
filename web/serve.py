import http.server
import socketserver
import webbrowser
import os

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.end_headers()

def start_server():
    # 切换到web目录
    web_dir = os.path.join(os.path.dirname(__file__))
    os.chdir(web_dir)
    
    PORT = 3000
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"前端服务器运行在 http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务器")
        
        # 自动打开浏览器
        webbrowser.open(f'http://localhost:{PORT}')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == '__main__':
    start_server()