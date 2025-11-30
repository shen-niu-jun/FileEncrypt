import ctypes
import os
import traceback

class EncryptorWrapper:
    def __init__(self, dll_path=None):
        try:
            if dll_path is None:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                dll_path = os.path.join(base_dir, "core", "FileEncryptCore.dll")
            
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"找不到DLL文件: {dll_path}")
            
            print(f"正在加载DLL: {dll_path}")
            
            # 使用WinDLL而不是CDLL
            self.lib = ctypes.WinDLL(dll_path)
            print("✓ DLL加载成功")
            
            self._setup_prototypes()
            
        except Exception as e:
            print(f"加密器初始化失败: {e}")
            traceback.print_exc()
            raise
    
    def _setup_prototypes(self):
        """设置C++函数的参数类型"""
        try:
            # 使用c_char_p而不是ctypes.c_char_p
            self.lib.processFile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
            self.lib.processFile.restype = ctypes.c_bool
            print("✓ 函数原型设置成功")
        except Exception as e:
            print(f"函数原型设置失败: {e}")
            raise
    
    def process_file(self, input_path, output_path, password):
        """处理文件（加密/解密）"""
        try:
            print(f"=== 处理文件 ===")
            print(f"输入: {input_path}")
            print(f"输出: {output_path}")
            print(f"密码长度: {len(password)}")
            
            # 验证输入文件
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
            input_size = os.path.getsize(input_path)
            print(f"输入文件大小: {input_size} 字节")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"创建输出目录: {output_dir}")
            
            # 使用系统默认编码（在Windows上通常是mbcs）
            result = self.lib.processFile(
                input_path.encode('mbcs'),
                output_path.encode('mbcs'),
                password.encode('utf-8')
            )
            
            print(f"DLL返回: {result}")
            
            if result:
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    print(f"输出文件大小: {output_size} 字节")
                    return True
                else:
                    print("警告: DLL返回成功但输出文件不存在")
                    return False
            else:
                print("DLL返回失败")
                return False
                
        except Exception as e:
            print(f"文件处理失败: {e}")
            traceback.print_exc()
            return False

# 简化测试函数
def quick_test():
    """快速测试"""
    try:
        print("快速测试DLL...")
        wrapper = EncryptorWrapper()
        
        # 创建简单测试文件
        import tempfile
        test_content = "快速测试"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            input_path = f.name
        
        output_path = input_path + ".encrypted"
        
        # 测试加密
        result = wrapper.process_file(input_path, output_path, "test123")
        print(f"快速测试结果: {result}")
        
        # 清理
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
        
        return result
        
    except Exception as e:
        print(f"快速测试失败: {e}")
        return False

if __name__ == '__main__':
    quick_test()