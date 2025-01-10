import glob
import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import chdir, copy, get, rm, rmdir
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime, check_min_vs

required_conan_version = ">=2.4"


class GStRtspServerConan(ConanFile):
    name = "gst-rtsp-server"
    description = "RTSP server library based on GStreamer"
    license = "LGPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gstreamer.freedesktop.org/"
    topics = ("gstreamer", "rtsp", "multimedia", "video", "audio", "broadcasting", "framework", "media")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_introspection": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_introspection": False,
    }
    languages = ["C"]
    implements = ["auto_shared_fpic"]

    def configure(self):
        self.options["gstreamer"].shared = self.options.shared
        self.options["gst-plugins-base"].shared = self.options.shared

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires(f"gstreamer/{self.version}", transitive_headers=True, transitive_libs=True)
        self.requires(f"gst-plugins-base/{self.version}", transitive_headers=True, transitive_libs=True)
        if self.options.with_introspection:
            self.requires("gobject-introspection/1.78.1")

    def validate(self):
        if (
            self.options.shared != self.dependencies["gstreamer"].options.shared
            or self.options.shared != self.dependencies["glib"].options.shared
            or self.options.shared != self.dependencies["gst-plugins-base"].options.shared
        ):
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("GLib, GStreamer and GstPlugins must be either all shared, or all static")
        if self.options.shared and is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration("shared build with static runtime is not supported due to the FlsAlloc limit")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = MesonToolchain(self)
        tc.project_options["examples"] = "disabled"
        tc.project_options["tests"] = "disabled"
        tc.project_options["doc"] = "disabled"
        tc.project_options["introspection"] = "enabled" if self.options.with_introspection else "disabled"
        tc.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def _fix_library_names(self, path):
        if is_msvc(self):
            with chdir(self, path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info(f"rename {filename_old} into {filename_new}")
                    shutil.move(filename_old, filename_new)

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        meson = Meson(self)
        meson.install()
        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "gstreamer-1.0", "pkgconfig"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):

        self.cpp_info.components["gstrtspserver-1.0"].requires = [
            "gstreamer::gstreamer-1.0",
            "gstreamer::gstreamer-base-1.0",
            "gstreamer::gstreamer-net-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-rtsp-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gst-plugins-base::gstreamer-sdp-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ]
        self.cpp_info.components["gstrtspserver-1.0"].set_property("pkg_config_name", "gstrtspserver-1.0")
        self.cpp_info.components["gstrtspserver-1.0"].includedirs = [os.path.join("include", "gstreamer-1.0")]
        self.cpp_info.components["gstrtspserver-1.0"].bindirs = []
        self.cpp_info.components["gstrtspserver-1.0"].libs = ["gstrtspserver-1.0"]
        if self.options.with_introspection:
            self.cpp_info.components["gstrtspserver-1.0"].requires.append("gobject-introspection::gobject-introspection")

        self.cpp_info.components["gstrtspclientsink"]

        self.cpp_info.components["rtspclientsink"].requires = [
            "gst-plugins-base::gstreamer-rtsp-1.0",
            "gst-plugins-base::gstreamer-sdp-1.0",
            "gstrtspserver-1.0",
        ]
        self.cpp_info.components["gstrtspclientsink"].includedirs = []
        self.cpp_info.components["gstrtspclientsink"].bindirs = []
        self.cpp_info.components["gstrtspclientsink"].resdirs = ["res"]
        if self.options.shared:
            self.cpp_info.components["gstrtspclientsink"].bindirs.append(os.path.join("lib", "gstreamer-1.0"))
        else:
            self.cpp_info.components["gstrtspclientsink"].defines.append("GST_RTSP_CLIENT_SINK_STATIC")
            self.cpp_info.components["gstrtspclientsink"].libs = ["gstrtspclientsink"]
            self.cpp_info.components["gstrtspclientsink"].libdirs = [os.path.join("lib", "gstreamer-1.0")]
