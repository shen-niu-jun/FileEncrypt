#pragma once

#ifdef ENCRYPTOR_EXPORTS
#define ENCRYPTOR_API __declspec(dllexport)
#else
#define ENCRYPTOR_API __declspec(dllimport)
#endif

// 使用 extern "C" 避免名称修饰，确保Python能正确找到函数
extern "C" {
    ENCRYPTOR_API bool processFile(const char* inputPath, const char* outputPath, const char* password);
    ENCRYPTOR_API bool processDirectory(const char* inputDir, const char* outputDir, const char* password);
}