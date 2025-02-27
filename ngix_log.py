#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 文件名: baixing_seo_processor.py
# 功能: 下载SEO日志，提取包含baidu的行，并转换为Excel格式

import os
import requests
import tarfile
import subprocess
import pandas as pd
from datetime import datetime


def download_file(url, save_path):
    """从指定URL下载文件"""
    print(f"正在从 {url} 下载文件...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        downloaded = 0

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # 显示下载进度
                    done = int(50 * downloaded / total_size)
                    print(
                        f"\r下载进度: [{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} 字节",
                        end="",
                    )

        print("\n下载完成!")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def extract_tarfile(tar_path, extract_dir):
    """解压缩tar.gz文件"""
    print(f"正在解压缩 {tar_path} 到 {extract_dir}...")
    try:
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)

        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)

        print("解压缩完成!")
        return True
    except Exception as e:
        print(f"解压缩失败: {e}")
        return False


def grep_baidu(directory, output_file):
    """使用grep查找包含baidu的行"""
    print(f"正在查找包含'baidu'的行...")
    try:
        # 使用grep递归搜索目录中所有文件
        cmd = f"grep -r 'baidu' {directory} > {output_file}"
        subprocess.run(cmd, shell=True, check=True)

        # 检查结果文件大小
        file_size = os.path.getsize(output_file)
        print(f"查找完成! 找到的结果已保存到 {output_file} (大小: {file_size} 字节)")
        return True
    except Exception as e:
        print(f"查找失败: {e}")
        return False


def convert_to_excel(text_file, excel_file):
    """将文本文件转换为Excel格式"""
    print(f"正在将 {text_file} 转换为Excel格式...")
    try:
        # 读取文本文件
        with open(text_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # 处理数据
        data = []
        for line in lines:
            # 分割行内容（按空格分割）
            parts = line.strip().split()

            # 移除每个部分中的引号
            cleaned_parts = []
            for part in parts:
                # 移除开头和结尾的引号（如果存在）
                if part.startswith('"') and part.endswith('"'):
                    part = part[1:-1]
                # 移除其他引号
                part = part.replace('"', "")
                cleaned_parts.append(part)

            data.append(cleaned_parts)

        # 确定最大列数
        max_cols = max(len(row) for row in data) if data else 0

        # 创建列名
        columns = [f"Column_{i+1}" for i in range(max_cols)]

        # 创建DataFrame
        df = pd.DataFrame(data, columns=columns)

        # 保存为Excel
        df.to_excel(excel_file, index=False, engine="openpyxl")

        print(f"转换完成! Excel文件已保存为 {excel_file}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def main():
    """主函数"""
    # 创建时间戳文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = f"baixing_seo_{timestamp}"
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    # 设置文件路径
    url = "http://examine.baixing.com/logs/baixing_seo.tar.gz"
    tar_file = os.path.join(work_dir, "baixing_seo.tar.gz")
    extract_dir = os.path.join(work_dir, "extracted")
    baidu_log = os.path.join(work_dir, "baidu_results.txt")
    excel_file = os.path.join(work_dir, "baidu_results.xlsx")

    # 执行任务
    if download_file(url, tar_file):
        if extract_tarfile(tar_file, extract_dir):
            if grep_baidu(extract_dir, baidu_log):
                convert_to_excel(baidu_log, excel_file)

    print(f"\n所有任务完成! 结果保存在目录: {work_dir}")
    print(f"Excel文件路径: {excel_file}")


if __name__ == "__main__":
    main()
