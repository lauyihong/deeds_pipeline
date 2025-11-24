#!/usr/bin/env python
"""
测试 Google APIs 配置
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 70)
print("🔍 检查 Google APIs 配置")
print("=" * 70)

# 加载 .env 文件
load_dotenv()

# 检查环境变量
print("\n📋 环境变量:")
print("-" * 70)

google_api_key = os.getenv("GOOGLE_API_KEY")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

if google_api_key:
    print(f"✅ GOOGLE_API_KEY: {google_api_key[:20]}...{google_api_key[-5:]}")
else:
    print("❌ GOOGLE_API_KEY: NOT SET")

if credentials_path:
    print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    # 检查文件是否存在
    if os.path.exists(credentials_path):
        print(f"   ✅ 文件存在")
    else:
        print(f"   ❌ 文件不存在！")
else:
    print("❌ GOOGLE_APPLICATION_CREDENTIALS: NOT SET")

if project_id:
    print(f"✅ GOOGLE_CLOUD_PROJECT: {project_id}")
else:
    print("❌ GOOGLE_CLOUD_PROJECT: NOT SET")

# 测试 Vision API
print("\n" + "=" * 70)
print("🔍 测试 Google Cloud Vision API")
print("=" * 70)

try:
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    print("✅ Vision API client 创建成功！")
    
except Exception as e:
    print(f"❌ Vision API 初始化失败:")
    print(f"   错误: {str(e)}")
    print(f"   类型: {type(e).__name__}")

# 测试 Gemini API
print("\n" + "=" * 70)
print("🔍 测试 Google Gemini API")
print("=" * 70)

try:
    import google.generativeai as genai
    
    if google_api_key:
        genai.configure(api_key=google_api_key)
        # 测试创建模型
        test_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        print("✅ Gemini API 配置成功！")
        print(f"   模型: gemini-2.0-flash-exp")
    else:
        print("❌ 无法配置 Gemini API: API key 未设置")
        
except Exception as e:
    print(f"❌ Gemini API 初始化失败:")
    print(f"   错误: {str(e)}")
    print(f"   类型: {type(e).__name__}")

# 总结
print("\n" + "=" * 70)
print("📊 配置状态总结")
print("=" * 70)

issues = []

if not google_api_key:
    issues.append("需要设置 GOOGLE_API_KEY (Gemini API)")
    
if not credentials_path or not os.path.exists(credentials_path):
    issues.append("需要配置 Google Cloud Vision 服务账号 JSON 密钥")

if issues:
    print("\n⚠️  发现以下问题:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n💡 解决方案:")
    if "GOOGLE_API_KEY" in str(issues):
        print("   - 访问 https://aistudio.google.com/app/apikey 获取 Gemini API key")
    if "Vision" in str(issues):
        print("   - 方案 A: 运行 'gcloud auth application-default login'")
        print("   - 方案 B: 下载服务账号 JSON 密钥并保存到项目目录")
else:
    print("\n🎉 所有 API 配置正确！")

print("=" * 70)

