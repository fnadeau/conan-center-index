from conans import ConanFile, tools, Meson, VisualStudioBuildEnvironment
from conans.errors import ConanInvalidConfiguration
from conan.tools.microsoft import msvc_runtime_flag
import glob
import os
import shutil


class GStPluginsBadConan(ConanFile):
    name = "gst-plugins-bad"
    description = "GStreamer is a development framework for creating applications like media players, video editors, " \
                  "streaming media broadcasters and so on"
    topics = ("gstreamer", "multimedia", "video", "audio", "broadcasting", "framework", "media")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gstreamer.freedesktop.org/"
    license = "GPL-2.0-only"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_introspection": [True, False],
        "with_gpl": [True, False]
        }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_introspection": False,
        "with_gpl": False
        }
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    exports_sources = ["patches/*.patch"]

    generators = "pkg_config"

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def validate(self):
        if self.options.shared != self.options["gstreamer"].shared or \
            self.options.shared != self.options["glib"].shared or \
            self.options.shared != self.options["gst-plugins-base"].shared:
                # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
                raise ConanInvalidConfiguration("GLib, GStreamer and GstPlugins must be either all shared, or all static")
        if tools.Version(self.version) >= "1.18.2" and\
           self.settings.compiler == "gcc" and\
           tools.Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration(
                "gst-plugins-bad %s does not support gcc older than 5" % self.version
            )
        if self.options.shared and str(msvc_runtime_flag(self)).startswith("MT"):
            raise ConanInvalidConfiguration('shared build with static runtime is not supported due to the FlsAlloc limit')

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        self.options['gstreamer'].shared = self.options.shared
        self.options['gst-plugins-base'].shared = self.options.shared

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def requirements(self):
        self.requires("glib/2.77.3")
        self.requires("gstreamer/%s" % self.version)
        self.requires("gst-libav/%s" % self.version)
        self.requires("gst-plugins-base/%s" % self.version)

    def build_requirements(self):
        self.build_requires("meson/1.2.1")
        if not tools.which("pkg-config"):
            self.build_requires("pkgconf/2.0.2")
        if self.settings.os == 'Windows':
            self.build_requires("winflexbison/2.5.24")
        else:
            self.build_requires("bison/3.8.2")
            self.build_requires("flex/2.6.4")
        if self.options.with_introspection:
            self.build_requires("gobject-introspection/1.72.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

    def _configure_meson(self):
        defs = dict()

        def add_flag(name, value):
            if name in defs:
                defs[name] += " " + value
            else:
                defs[name] = value

        def add_compiler_flag(value):
            add_flag("c_args", value)
            add_flag("cpp_args", value)

        def add_linker_flag(value):
            add_flag("c_link_args", value)
            add_flag("cpp_link_args", value)

        meson = Meson(self)
        if self.settings.compiler == "Visual Studio":
            add_linker_flag("-lws2_32")
            add_compiler_flag("-%s" % self.settings.compiler.runtime)
            if int(str(self.settings.compiler.version)) < 14:
                add_compiler_flag("-Dsnprintf=_snprintf")
        if self.settings.get_safe("compiler.runtime"):
            defs["b_vscrt"] = str(self.settings.compiler.runtime).lower()
        #defs["tools"] = "disabled"
        defs["examples"] = "disabled"
        #defs["benchmarks"] = "disabled"
        defs["tests"] = "disabled"
        defs["wrap_mode"] = "nofallback"
        defs["introspection"] = "enabled" if self.options.with_introspection else "disabled"
        defs["gpl"] = "enabled" if self.options.with_gpl else "disabled"
        meson.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        defs=defs)
        return meson

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.build()

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.install()

        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "gstreamer-1.0", "pkgconfig"))
        tools.remove_files_by_mask(self.package_folder, "*.pdb")

    def package_info(self):

        plugins = [["accurip", ["gstreamer::gstreamer-1.0", "gst-plugins-base::gstreamer-audio-1.0"],[]],
                   ["adpcmdec", ["gstreamer::gstreamer-1.0", "gst-plugins-base::gstreamer-audio-1.0"],[]],
                   ["adpcmenc", ["gstreamer::gstreamer-1.0"],[]],
                   ["aes", ["gstreamer::gstreamer-1.0"],[]],
                   ["aiff", ["gstreamer::gstreamer-1.0"],[]],
                   ["asfmux", ["gstreamer::gstreamer-1.0"],[]],
                   ["audiobuffersplit", ["gstreamer::gstreamer-1.0"],[]],
                   ["audiofxbad", ["gstreamer::gstreamer-1.0"],[]],
                   ["audiolatency", ["gstreamer::gstreamer-1.0"],[]],
                   ["audiomixmatrix", ["gstreamer::gstreamer-1.0"],[]],
                   ["audiovisualizers", ["gstreamer::gstreamer-1.0"],[]],
                   ["autoconvert", ["gstreamer::gstreamer-1.0"],[]],
                   ["bayer", ["gstreamer::gstreamer-1.0"],[]],
                   ["bz2", ["gstreamer::gstreamer-1.0"],[]],
                   ["camerabin", ["gstreamer::gstreamer-1.0"],[]],
                   ["closedcaption", ["gstreamer::gstreamer-1.0"],[]],
                   ["codecalpha", ["gstreamer::gstreamer-1.0"],[]],
                   ["codectimestamper", ["gstreamer::gstreamer-1.0"],[]],
                   ["coloreffects", ["gstreamer::gstreamer-1.0"],[]],
                   ["curl", ["gstreamer::gstreamer-1.0"],[]],
                   ["dash", ["gstreamer::gstreamer-1.0"],[]],
                   ["dc1394", ["gstreamer::gstreamer-1.0"],[]],
                   ["debugutilsbad", ["gstreamer::gstreamer-1.0"],[]],
                   ["decklink", ["gstreamer::gstreamer-1.0"],[]],
                   ["dtls", ["gstreamer::gstreamer-1.0"],[]],
                   ["dvb", ["gstreamer::gstreamer-1.0"],[]],
                   ["dvbsubenc", ["gstreamer::gstreamer-1.0"],[]],
                   ["dvbsuboverlay", ["gstreamer::gstreamer-1.0"],[]],
                   ["dvdspu", ["gstreamer::gstreamer-1.0"],[]],
                   ["faceoverlay", ["gstreamer::gstreamer-1.0"],[]],
                   ["fbdevsink", ["gstreamer::gstreamer-1.0"],[]],
                   ["festival", ["gstreamer::gstreamer-1.0"],[]],
                   ["fieldanalysis", ["gstreamer::gstreamer-1.0"],[]],
                   ["freeverb", ["gstreamer::gstreamer-1.0"],[]],
                   ["frei0r", ["gstreamer::gstreamer-1.0"],[]],
                   ["gaudieffects", ["gstreamer::gstreamer-1.0"],[]],
                   ["gdp", ["gstreamer::gstreamer-1.0"],[]],
                   ["geometrictransform", ["gstreamer::gstreamer-1.0"],[]],
                   ["gtkwayland", ["gstreamer::gstreamer-1.0"],[]],
                   ["hls", ["gstreamer::gstreamer-1.0"],[]],
                   ["id3tag", ["gstreamer::gstreamer-1.0"],[]],
                   ["inter", ["gstreamer::gstreamer-1.0"],[]],
                   ["interlace", ["gstreamer::gstreamer-1.0"],[]],
                   ["ipcpipeline", ["gstreamer::gstreamer-1.0"],[]],
                   ["ivfparse", ["gstreamer::gstreamer-1.0"],[]],
                   ["ivtc", ["gstreamer::gstreamer-1.0"],[]],
                   ["jp2kdecimator", ["gstreamer::gstreamer-1.0"],[]],
                   ["jpegformat", ["gstreamer::gstreamer-1.0"],[]],
                   ["kms", ["gstreamer::gstreamer-1.0"],[]],
                   ["legacyrawparse", ["gstreamer::gstreamer-1.0"],[]],
                   ["midi", ["gstreamer::gstreamer-1.0"],[]],
                   ["mpegpsdemux", ["gstreamer::gstreamer-1.0", "gstreamer::gstreamer-base-1.0", "gst-plugins-base::gstreamer-pbutils-1.0"],[]],
                   ["mpegpsmux", ["gstreamer::gstreamer-1.0"],[]],
                   ["mpegtsdemux", ["gstreamer::gstreamer-1.0", "gst-plugins-base::gstreamer-tag-1.0", "gst-plugins-base::gstreamer-pbutils-1.0", "gst-plugins-base::gstreamer-audio-1.0", "gstreamer-codecparsers-1.0", "gstreamer-mpegts-1.0"],["m"] if self.settings.os == "Linux" else []],
                   ["mpegtsmux", ["gstreamer::gstreamer-1.0", "gst-plugins-base::gstreamer-tag-1.0", "gst-plugins-base::gstreamer-pbutils-1.0", "gst-plugins-base::gstreamer-audio-1.0", "gst-plugins-base::gstreamer-video-1.0", "gstreamer-mpegts-1.0"],[]],
                   ["mxf", ["gstreamer::gstreamer-1.0"],[]],
                   ["netsim", ["gstreamer::gstreamer-1.0"],[]],
                   ["nvcodec", ["gstreamer::gstreamer-1.0"],[]],
                   ["opencv", ["gstreamer::gstreamer-1.0"],[]],
                   ["openexr", ["gstreamer::gstreamer-1.0"],[]],
                   ["openjpeg", ["gstreamer::gstreamer-1.0"],[]],
                   ["openni2", ["gstreamer::gstreamer-1.0"],[]],
                   ["opusparse", ["gstreamer::gstreamer-1.0"],[]],
                   ["pcapparse", ["gstreamer::gstreamer-1.0"],[]],
                   ["pnm", ["gstreamer::gstreamer-1.0"],[]],
                   ["proxy", ["gstreamer::gstreamer-1.0"],[]],
                   #["qsv", ["gstreamer::gstreamer-1.0"],[]],
                   ["removesilence", ["gstreamer::gstreamer-1.0"],[]],
                   ["rfbsrc", ["gstreamer::gstreamer-1.0"],[]],
                   ["rist", ["gstreamer::gstreamer-1.0"],[]],
                   ["rtmp2", ["gstreamer::gstreamer-1.0"],[]],
                   ["rtpmanagerbad", ["gstreamer::gstreamer-1.0"],[]],
                   ["rtponvif", ["gstreamer::gstreamer-1.0"],[]],
                   ["sctp", ["gstreamer::gstreamer-1.0"],[]],
                   ["sdpelem", ["gstreamer::gstreamer-1.0"],[]],
                   ["segmentclip", ["gstreamer::gstreamer-1.0"],[]],
                   ["shm", ["gstreamer::gstreamer-1.0"],[]],
                   ["siren", ["gstreamer::gstreamer-1.0"],[]],
                   ["smooth", ["gstreamer::gstreamer-1.0"],[]],
                   ["smoothstreaming", ["gstreamer::gstreamer-1.0"],[]],
                   ["speed", ["gstreamer::gstreamer-1.0"],[]],
                   ["subenc", ["gstreamer::gstreamer-1.0"],[]],
                   ["switchbin", ["gstreamer::gstreamer-1.0"],[]],
                   ["timecode", ["gstreamer::gstreamer-1.0"],[]],
                   ["transcode", ["gstreamer::gstreamer-1.0"],[]],
                   ["ttmlsubs", ["gstreamer::gstreamer-1.0"],[]],
                   #["va", ["gstreamer::gstreamer-1.0"],[]],
                   ["videofiltersbad", ["gstreamer::gstreamer-1.0"],[]],
                   ["videoframe_audiolevel", ["gstreamer::gstreamer-1.0"],[]],
                   ["videoparsersbad", ["gstreamer::gstreamer-1.0", "gstreamer::gstreamer-base-1.0", "gst-plugins-base::gstreamer-pbutils-1.0", "gst-libav::gst-libav", "gstreamer-codecparsers-1.0"],[]],
                   ["videosignal", ["gstreamer::gstreamer-1.0"],[]],
                   ["vmnc", ["gstreamer::gstreamer-1.0"],[]],
                   ["waylandsink", ["gstreamer::gstreamer-1.0"],[]],
                   ["webp", ["gstreamer::gstreamer-1.0"],[]],
                   ["y4mdec", ["gstreamer::gstreamer-1.0"],[]]]

        gst_plugins = []
        gst_plugin_path = os.path.join(self.package_folder, "lib", "gstreamer-1.0")
        gst_include_path = os.path.join(self.package_folder, "include", "gstreamer-1.0")

        pkgconfig_variables = {
            "exec_prefix": "${prefix}",
            "toolsdir": "${exec_prefix}/bin",
            "pluginsdir": "${libdir}/gstreamer-1.0",
            "datarootdir": "${prefix}/share",
            "datadir": "${datarootdir}",
            "girdir": "${datadir}/gir-1.0",
            "typelibdir": "${libdir}/girepository-1.0",
            "libexecdir": "${prefix}/libexec"
        }
        pkgconfig_custom_content = "\n".join("{}={}".format(key, value) for key, value in pkgconfig_variables.items())

        if self.options.shared:
            self.output.info("Appending GST_PLUGIN_PATH env var : %s" % gst_plugin_path)
            self.runenv_info.prepend_path("GST_PLUGIN_PATH", gst_plugin_path)
            self.env_info.GST_PLUGIN_PATH.append(gst_plugin_path)

        for plugin in plugins:
            gst_lib_name = "gst%s" % plugin[0]
            self.cpp_info.components[gst_lib_name].libs = [gst_lib_name]
            self.cpp_info.components[gst_lib_name].libdirs.append(gst_plugin_path)
            self.cpp_info.components[gst_lib_name].requires = plugin[1]
            self.cpp_info.components[gst_lib_name].system_libs = plugin[2]
            gst_plugins.append(gst_lib_name)

        # Libraries
        self.cpp_info.components["gstreamer-plugins-bad-1.0"].names["pkg_config"] = "gstreamer-plugins-bad-1.0"
        self.cpp_info.components["gstreamer-plugins-bad-1.0"].requires = ["gstreamer::gstreamer-1.0"]
        self.cpp_info.components["gstreamer-plugins-bad-1.0"].includedirs = [gst_include_path]
        if not self.options.shared:
            self.cpp_info.components["gstreamer-plugins-bad-1.0"].defines.append("GST_PLUGINS_BAD_STATIC")
            self.cpp_info.components["gstreamer-plugins-bad-1.0"].requires.extend(gst_plugins)
        else:
            self.cpp_info.components["gstreamer-plugins-bad-1.0"].bindirs.append(gst_plugin_path)
        self.cpp_info.components["gstreamer-plugins-bad-1.0"].set_property("pkg_config_custom_content", pkgconfig_custom_content)

        plugin_libs = [["adaptivedemux-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["badaudio-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["basecamerabinsrc-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["codecparsers-1.0", ["gstreamer::gstreamer-1.0"],["m"] if self.settings.os == "Linux" else []],
                       ["codecs-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["cuda-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["insertbin-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["isoff-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["mpegts-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["opencv-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["photography-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["play-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["player-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["sctp-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["transcoder-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["uridownloader-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       #["va-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["wayland-1.0", ["gstreamer::gstreamer-1.0"],[]],
                       ["webrtc-1.0", ["gstreamer::gstreamer-1.0"],[]]]

        for plugin_lib in plugin_libs:
            component_name = "gstreamer-%s" % plugin_lib[0]
            lib_name = "gst%s" % plugin_lib[0]
            self.cpp_info.components[component_name].names["pkg_config"] = component_name
            self.cpp_info.components[component_name].libs = [lib_name]
            self.cpp_info.components[component_name].requires = plugin_lib[1]
            self.cpp_info.components[component_name].system_libs = plugin_lib[2]
            self.cpp_info.components[component_name].includedirs = [gst_include_path]
        if not self.options.shared:
            self.cpp_info.components[component_name].defines.append("GST_PLUGINS_BAD_STATIC")
            self.cpp_info.components[component_name].requires.extend(gst_plugins)
        else:
            self.cpp_info.components[component_name].bindirs.append(gst_plugin_path)
            self.cpp_info.components[component_name].set_property("pkg_config_custom_content", pkgconfig_custom_content)

#        gst_plugin_path = os.path.join(self.package_folder, "lib", "gstreamer-1.0")
#        if self.options.shared:
#            self.output.info("Appending GST_PLUGIN_PATH env var : %s" % gst_plugin_path)
#            self.cpp_info.bindirs.append(gst_plugin_path)
#            self.runenv_info.prepend_path("GST_PLUGIN_PATH", gst_plugin_path)
#            self.env_info.GST_PLUGIN_PATH.append(gst_plugin_path)
#        else:
#            self.cpp_info.defines.append("GST_PLUGINS_BAD_STATIC")
#            self.cpp_info.libdirs.append(gst_plugin_path)
#            self.cpp_info.libs.extend(["gst%s" % plugin for plugin in plugins])
#
#        self.cpp_info.includedirs = ["include", os.path.join("include", "gstreamer-1.0")]
#
#        self.cpp_info.components["gstreamer-mpegts-1.0"].names["pkg_config"] = "gstreamer-mpegts-1.0"
#        self.cpp_info.components["gstreamer-mpegts-1.0"].libs = ["gstmpegts-1.0"]
#        self.cpp_info.components["gstreamer-mpegts-1.0"].requires = ["gst-plugins-bad::gst-plugins-bad"]
#        self.cpp_info.components["gstreamer-mpegts-1.0"].includedirs = [os.path.join("include", "gstreamer-1.0")]
#        #self.cpp_info.components["gstreamer-mpegts-1.0"].set_property("pkg_config_custom_content", pkgconfig_custom_content)
#
