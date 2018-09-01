from conans import ConanFile, tools, CMake, AutoToolsBuildEnvironment
from conans.util import files
import os


class ZlibConan(ConanFile):
    name = "minizip"
    version = "1.2.11"
    ZIP_FOLDER_NAME = "zlib-%s" % version
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports_sources = ["CMakeLists.txt"]
    # url = "http://github.com/lasote/conan-zlib"
    # license = "http://www.zlib.net/zlib_license.html"
    description = "A Massively Spiffy Yet Delicately Unobtrusive Compression Library " \
                  "(Also Free, Not to Mention Unencumbered by Patents)"

    def configure(self):
      del self.settings.compiler.libcxx

    def source(self):
      z_name = "zlib-%s.tar.gz" % self.version
      tools.download("https://zlib.net/zlib-%s.tar.gz" % self.version, z_name)
      tools.unzip(z_name)
      os.unlink(z_name)
      if not tools.os_info.is_windows:
        self.run("chmod +x ./%s/configure" % self.ZIP_FOLDER_NAME)
      
      os.rename(self.ZIP_FOLDER_NAME, 'src')

    def build(self):
      cmake = CMake(self, parallel=True)
      cmake.definitions["ENABLE_MINIZIP:BOOL"] = True
      cmake.configure()
      cmake.build()

    def package(self):
      # Headers
      self.copy("*zlib.h", dst="include", keep_path=False)
      self.copy("*zconf.h", dst="include", keep_path=False)
      self.copy("*zip.h", dst="include/minizip", keep_path=False)
      self.copy("*unzip.h", dst="include/minizip", keep_path=False)
      self.copy("*minizip_extern.h", dst="include/minizip", keep_path=False)
      self.copy("*crypt.h", dst="include/minizip", keep_path=False)
      self.copy("*mztools.h", dst="include/minizip", keep_path=False)
      self.copy("*ioapi.h", dst="include/minizip", keep_path=False)
      if self.settings.os == "Windows":
          self.copy("*iowin32.h", dst="include/minizip", keep_path=False)
      # Libraries
      self.copy("*.dll", dst="bin", keep_path=False)
      self.copy("*.lib", dst="lib", keep_path=False)
      self.copy("*.so*", dst="lib", keep_path=False, symlinks=True)
      self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        libs = None
        if self.settings.os == "Windows":
            libs = ["zlib", "minizip"]
            if self.options.shared:
                self.cpp_info.defines =  ["ZLIB_DLL", "MINIZIP_DLL"]
            else:
                libs = [i + "static" for i in libs]
            if self.settings.build_type == "Debug":
                libs = [i + "d" for i in libs]
            libs = [i + ".lib" for i in libs]
        else:
            libs = ["z", "minizip"]
        self.cpp_info.libs = libs
        self.cpp_info.includedirs = ['include', 'include/minizip']  # Ordered list of include paths
        self.cpp_info.libdirs = ['lib']  # Directories where libraries can be found

        
