from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get, apply_conandata_patches, export_conandata_patches, replace_in_file, rmdir
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=1.52.0"

class QtADS(ConanFile):
    name = "qt-advanced-docking-system"
    license = "LGPL-2.1"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System"
    topics = ("qt", "gui")
    description = (
        "Qt Advanced Docking System lets you create customizable layouts "
        "using a full featured window docking system similar to what is found "
        "in many popular integrated development environments (IDEs) such as "
        "Visual Studio."
    )
    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _qt_major(self):
        return Version(self.dependencies["qt"].ref.version).major

    @property
    def _qt_semver(self):
        return Version(self.dependencies["qt"].ref.version)

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qt/[>=5.15.7 <7]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if not (self.dependencies["qt"].options.gui and self.dependencies["qt"].options.widgets):
            raise ConanInvalidConfiguration(f"{self.ref} requires qt gui and widgets")
        
        if self._qt_major >= 6 and Version(self.version) < "4.0.3":
            raise ConanInvalidConfiguration(f"qt-advanced-docking-system v{self.version} does not support Qt6")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ADS_VERSION"] = self.version
        tc.variables["BUILD_EXAMPLES"] = "OFF"
        tc.variables["BUILD_STATIC"] = not self.options.shared

        if Version(self.version) >= "4.0.4":
            tc.variables["QT_VERSION_MAJOR"] = f"{self._qt_major}"

        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        replace_in_file(self,
            os.path.join(self.source_folder, "src", "ads_globals.cpp"),
            "#include <qpa/qplatformnativeinterface.h>",
            f"#include <{self._qt_semver}/QtGui/qpa/qplatformnativeinterface.h>"
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, pattern="gnu-lgpl-v2.1.md", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "license"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        # Starting with 4.0.3, libname has QT major version in it
        target = "qtadvanceddocking" if Version(self.version) < "4.0.3" else  f"qt{self._qt_major}advanceddocking"
        libname = target + str("d" if is_msvc(self) and self.settings.build_type == "Debug" else "")

        self.cpp_info.set_property("cmake_file_name", "ads")
        self.cpp_info.set_property("cmake_target_name", f"ads::{target}")
        self.cpp_info.requires = ["qt::qtCore", "qt::qtGui", "qt::qtWidgets"]

        # Starting with 4.0.3, libs are in include/${library_name}
        if Version(self.version) >= "4.0.3":
            self.cpp_info.includedirs.append(os.path.join("include", target))

        if self.options.shared:
            self.cpp_info.libs = [libname]
        else:
            self.cpp_info.defines.append("ADS_STATIC")
            self.cpp_info.libs = [f"{libname}_static"]
