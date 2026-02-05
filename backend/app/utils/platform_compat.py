"""
平台兼容性模块

为 Windows 平台提供 Unix/Linux 特有模块的 mock 实现。
"""

import platform
import sys

# 如果在 Windows 平台上，mock pwd 和 grp 模块
if platform.system() == "Windows":
    # Mock pwd 模块
    class PwdModule:
        """Mock pwd 模块用于 Windows 平台"""

        class struct_passwd:
            """Mock passwd 结构"""

            def __init__(self):
                self.pw_name = "user"
                self.pw_passwd = "x"
                self.pw_uid = 1000
                self.pw_gid = 1000
                self.pw_gecos = ""
                self.pw_dir = "/home/user"
                self.pw_shell = "/bin/bash"

        @staticmethod
        def getpwuid(uid):
            """Mock getpwuid 函数"""
            return PwdModule.struct_passwd()

        @staticmethod
        def getpwnam(name):
            """Mock getpwnam 函数"""
            return PwdModule.struct_passwd()

    # Mock grp 模块
    class GrpModule:
        """Mock grp 模块用于 Windows 平台"""

        class struct_group:
            """Mock group 结构"""

            def __init__(self):
                self.gr_name = "group"
                self.gr_passwd = "x"
                self.gr_gid = 1000
                self.gr_mem = []

        @staticmethod
        def getgrgid(gid):
            """Mock getgrgid 函数"""
            return GrpModule.struct_group()

        @staticmethod
        def getgrnam(name):
            """Mock getgrnam 函数"""
            return GrpModule.struct_group()

    # 将 mock 模块注入到 sys.modules
    sys.modules["pwd"] = PwdModule()
    sys.modules["grp"] = GrpModule()
