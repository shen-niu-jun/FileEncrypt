#include "pch.h"
#include "encryptor.h"
#include <fstream>
#include <vector>
#include <string>
#include <filesystem>

// 简单的XOR加密函数
void xorEncryptDecrypt(std::vector<unsigned char>& data, const std::vector<unsigned char>& key) {
    for (size_t i = 0; i < data.size(); i++) {
        data[i] ^= key[i % key.size()];
    }
}

// 生成基于密码的密钥
std::vector<unsigned char> generateKey(const std::string& password, int keyLength = 32) {
    std::vector<unsigned char> key(keyLength);

    // 更复杂的密钥生成算法
    for (int i = 0; i < keyLength; i++) {
        key[i] = static_cast<unsigned char>(
            password[i % password.length()] ^
            (i * 17 + 31) ^
            (password.length() * 7)
            );
    }

    return key;
}

// 导出函数 - 处理单个文件
ENCRYPTOR_API bool processFile(const char* inputPath, const char* outputPath, const char* password) {
    try {
        // 验证输入参数
        if (!inputPath || !outputPath || !password) {
            return false;
        }

        std::string inputStr(inputPath);
        std::string outputStr(outputPath);
        std::string passwordStr(password);

        if (inputStr.empty() || outputStr.empty() || passwordStr.empty()) {
            return false;
        }

        // 检查输入文件是否存在
        if (!std::filesystem::exists(inputStr)) {
            return false;
        }

        // 读取文件
        std::ifstream inputFile(inputStr, std::ios::binary);
        if (!inputFile.is_open()) {
            return false;
        }

        // 获取文件大小
        inputFile.seekg(0, std::ios::end);
        size_t fileSize = inputFile.tellg();
        inputFile.seekg(0, std::ios::beg);

        // 读取文件数据
        std::vector<unsigned char> fileData(fileSize);
        if (!inputFile.read(reinterpret_cast<char*>(fileData.data()), fileSize)) {
            inputFile.close();
            return false;
        }
        inputFile.close();

        // 生成密钥
        auto key = generateKey(passwordStr);

        // 加密/解密数据
        xorEncryptDecrypt(fileData, key);

        // 确保输出目录存在
        std::filesystem::path outputPathObj(outputStr);
        auto outputDir = outputPathObj.parent_path();
        if (!outputDir.empty() && !std::filesystem::exists(outputDir)) {
            std::filesystem::create_directories(outputDir);
        }

        // 写入输出文件
        std::ofstream outputFile(outputStr, std::ios::binary);
        if (!outputFile.is_open()) {
            return false;
        }

        outputFile.write(reinterpret_cast<const char*>(fileData.data()), fileData.size());

        if (!outputFile.good()) {
            outputFile.close();
            return false;
        }

        outputFile.close();
        return true;
    }
    catch (const std::exception&) {
        // 捕获所有异常，返回false
        return false;
    }
    catch (...) {
        // 捕获其他所有异常
        return false;
    }
}

// 导出函数 - 处理目录
ENCRYPTOR_API bool processDirectory(const char* inputDir, const char* outputDir, const char* password) {
    try {
        if (!inputDir || !outputDir || !password) {
            return false;
        }

        std::string inputStr(inputDir);
        std::string outputStr(outputDir);
        std::string passwordStr(password);

        if (inputStr.empty() || outputStr.empty() || passwordStr.empty()) {
            return false;
        }

        if (!std::filesystem::exists(inputStr) || !std::filesystem::is_directory(inputStr)) {
            return false;
        }

        // 创建输出目录
        std::filesystem::create_directories(outputStr);

        bool allSuccess = true;

        // 遍历目录中的所有文件
        for (const auto& entry : std::filesystem::recursive_directory_iterator(inputStr)) {
            if (entry.is_regular_file()) {
                std::string inputPath = entry.path().string();

                // 计算相对路径
                std::string relativePath = std::filesystem::relative(entry.path(), inputStr).string();
                std::string outputPath = (std::filesystem::path(outputStr) / relativePath).string();

                // 创建子目录
                std::filesystem::create_directories(std::filesystem::path(outputPath).parent_path());

                // 处理文件
                if (!processFile(inputPath.c_str(), outputPath.c_str(), password)) {
                    allSuccess = false;
                }
            }
        }

        return allSuccess;
    }
    catch (const std::exception&) {
        return false;
    }
    catch (...) {
        return false;
    }
}