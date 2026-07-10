#!/usr/bin/env python3
"""
Gmail SMTP Connection Test - Test if proxy node supports Gmail SMTP
"""

import os
import socket
import sys
import time

def test_proxy_connection(proxy_host, proxy_port, smtp_server, smtp_port):
    """Test TCP connection through SOCKS5 proxy."""
    try:
        import socks

        print(f"🔍 测试代理连接...")
        print(f"   代理: {proxy_host}:{proxy_port}")
        print(f"   目标: {smtp_server}:{smtp_port}")

        # Create SOCKS5 socket
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
        sock.settimeout(10)

        # Try to connect
        start_time = time.time()
        sock.connect((smtp_server, smtp_port))
        connect_time = time.time() - start_time

        print(f"✅ TCP连接成功！ (耗时: {connect_time:.2f}秒)")

        # Test SSL handshake for port 465
        if smtp_port == 465:
            try:
                import ssl
                context = ssl.create_default_context()
                ssl_sock = context.wrap_socket(sock, server_hostname=smtp_server)
                print(f"✅ SSL握手成功！")
                ssl_sock.close()
                return True
            except Exception as e:
                print(f"❌ SSL握手失败: {e}")
                sock.close()
                return False
        else:
            # For port 587, just test TCP connection
            sock.close()
            return True

    except ImportError:
        print("❌ 错误: 需要安装 PySocks")
        print("   安装命令: pip install pysocks")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def main():
    proxy_str = os.environ.get('SMTP_SOCKS_PROXY', 'socks5://127.0.0.1:7897')

    # Parse proxy string
    proxy_str = proxy_str.replace('socks5://', '')
    if ':' in proxy_str:
        proxy_host, proxy_port = proxy_str.rsplit(':', 1)
        proxy_port = int(proxy_port)
    else:
        proxy_host = proxy_str
        proxy_port = 1080

    print("=" * 60)
    print("📧 Gmail SMTP 代理连接测试")
    print("=" * 60)
    print()

    # Test port 465 (SMTP_SSL)
    print("【测试1】端口 465 (SMTP_SSL)")
    print("-" * 60)
    result_465 = test_proxy_connection(proxy_host, proxy_port, 'smtp.gmail.com', 465)
    print()

    # Test port 587 (STARTTLS)
    print("【测试2】端口 587 (STARTTLS)")
    print("-" * 60)
    result_587 = test_proxy_connection(proxy_host, proxy_port, 'smtp.gmail.com', 587)
    print()

    # Summary
    print("=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"端口 465 (SMTP_SSL): {'✅ 可用' if result_465 else '❌ 不可用'}")
    print(f"端口 587 (STARTTLS): {'✅ 可用' if result_587 else '❌ 不可用'}")
    print()

    if result_587:
        print("🎉 好消息！端口587可用，Hermes Agent应该可以正常发送邮件")
        print("   建议：确保send_email.py中 SMTP_PORT = 587")
    elif result_465:
        print("⚠️  只有端口465可用，可能需要调整配置")
        print("   建议：考虑切换到其他代理节点")
    else:
        print("❌ 两个端口都不可用")
        print("   建议：切换代理节点（推荐香港/美国/日本节点）")

    print()

if __name__ == "__main__":
    main()
