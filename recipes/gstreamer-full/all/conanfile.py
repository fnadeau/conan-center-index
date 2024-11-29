from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, chdir, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
import glob
import os
import shutil

required_conan_version = ">=2.3.0"

# From subprojects/gst-plugins-base/meson_options.txt
GST_BASE_MESON_OPTIONS = {
    'adder',
    'app',
    'audioconvert',
    'audiomixer',
    'audiorate',
    'audioresample',
    'audiotestsrc',
    'compositor',
    'debugutils',
    'drm',
    'dsd',
    'encoding',
    'gio',
    'gio-typefinder',
    'overlaycomposition',
    'pbtypes',
    'playback',
    'rawparse',
    'subparse',
    'tcp',
    'typefind',
    'videoconvertscale',
    'videorate',
    'videotestsrc',
    'volume',
}

GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS = {
    'alsa',
#    'cdparanoia', # cdparanoia is not available in conan-center
#    'libvisual', # libvisual is not available in conan-center
    'ogg',
    'opus',
    'pango',
    'theora',
#    #'tremor', # tremor is not available in conan-center
    'vorbis',
    'x11',
    'xshm',
    'xvideo',
    'xi',
}

GST_BASE_MESON_OPTIONS_GL = {
    'gl',
    'gl_graphene',
    'gl_png',
}

GST_GOOD_MESON_OPTIONS = {
    'alpha',
    'apetag',
    'audiofx',
    'audioparsers',
    'auparse',
    'autodetect',
    'avi',
    'cutter',
    'debugutils',
    'deinterlace',
    'dtmf',
    'effectv',
    'equalizer',
    'flv',
    'flx',
    'goom',
    'goom2k1',
    'icydemux',
    'id3demux',
    'imagefreeze',
    'interleave',
    'isomp4',
    'law',
    'level',
    'matroska',
    'monoscope',
    'multifile',
    'multipart',
    'replaygain',
    'rtp',
    'rtpmanager',
    'rtsp',
    'shapewipe',
    'smpte',
    'spectrum',
    'udp',
    'videobox',
    'videocrop',
    'videofilter',
    'videomixer',
    'wavenc',
    'wavparse',
    'xingmux',
    'y4m',
}

GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS = {
#    'adaptivedemux2',
#    'aalib',
#    'amrnb',
#    'amrwbdec',
    'bz2',
#    'cairo',
#    'directsound',
#    'dv',
#    'dv1394',
    'flac',
    'gdk-pixbuf',
#    'gtk3',
#    'jack',
#    'jpeg',
    'lame',
#    'libcaca',
    'mpg123',
#    'oss',
#    'oss4',
#    'osxaudio',
#    'osxvideo',
#    'png',
#    'pulse',
#    'shout2',
#    'speex',
    'taglib',
#    'twolame',
    'vpx',
#    'waveform',
#    'wavpack',
}

# TODO check bad list
GST_BAD_MESON_OPTIONS = {
    'accurip',
    'adpcmdec',
    'adpcmenc',
    'aiff',
    'asfmux',
    'audiobuffersplit',
    'audiofxbad',
    'audiomixmatrix',
    'audiolatency',
    'audiovisualizers',
    'autoconvert',
    'bayer',
    'camerabin2',
    'codecalpha',
    'codectimestamper',
    'coloreffects',
    'debugutils',
    'dvbsubenc',
    'dvbsuboverlay',
    'dvdspu',
    'faceoverlay',
    'festival',
    'fieldanalysis',
    'freeverb',
    'frei0r',
    'gaudieffects',
    'gdp',
    'geometrictransform',
    'id3tag',
    'insertbin',
    'inter',
    'interlace',
    'ivfparse',
    'ivtc',
    'jp2kdecimator',
    'jpegformat',
    #'librfb',
    'midi',
    'mpegdemux',
    'mpegpsmux',
    'mpegtsdemux',
    'mpegtsmux',
    'mse',
    'mxf',
    'netsim',
    'onvif',
    'pcapparse',
    'pnm',
    'proxy',
    'rawparse',
    'removesilence',
    'rist',
    'rtmp2',
    'rtp',
    'sdp',
    'segmentclip',
    'siren',
    'smooth',
    'speed',
    'subenc',
    'switchbin',
    'timecode', # TODO handle LTC dependency
    'transcode',
    'unixfd',
    'videofilters',
    'videoframe_audiolevel',
    'videoparsers',
    'videosignal',
    'vmnc',
    'y4m',
}

GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS = {
    #'aes',
    #'analyticsoverlay',
    #'assrender',
    #'aom',
    #'avtp',
    #'bs2b',
    #'bz2',
    #'chromaprint',
    #'closedcaption',
    #'codec2json',
    #'colormanagement',
    #'curl',
    #'dash',
    #'dc1394',
    #'directfb',
    #'dtls',
    #'dts',
    #'faac',
    #'faad',
    #'fdkaac',
    #'flite',
    #'fluidsynth',
    #'gme',
    #'gs',
    #'gsm',
    #'gtk',
    #'hls',
    #'iqa',
    #'isac',
    #'ladspa',
    #'lc3',
    #'ldac',
    #'libde265',
    #'lv2',
    #'mdns',
    #'modplug',
    #'mpeg2enc',
    #'mplex',
    #'musepack',
    #'neon',
    #'onnx',
    #'openal',
    #'openaptx',
    #'opencv',
    #'openexr',
    #'openh264',
    #'openjpeg',
    #'openmpt',
    #'openni2',
    #'opus',
    #'qroverlay',
    #'qt6d3d11',
    #'resindvd',
    #'rsvg',
    #'rtmp',
    #'sbc',
    #'sctp',
    #'smoothstreaming',
    #'sndfile',
    #'soundtouch',
    #'spandsp',
    #'srt',
    #'srtp',
    #'svtav1',
    #'svthevcenc',
    #'teletextdec',
    #'ttml',
    #'voaacenc',
    #'voamrwbenc',
    #'vulkan',
    #'wayland',
    #'webrtc',
    #'webrtcdsp',
    #'webp',
    #'wildmidi',
    #'wpe',
    #'x265',
    #'zxing',
    #'zbar',
}

GST_UGLY_MESON_OPTIONS = {
    'asfdemux',
    'dvdlpcmdec',
    'dvdsub',
    'realmedia',
}

GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS = {
    #'a52dec',
    #'cdio',
    #'dvdread',
    #'mpeg2dec',
    #'sidplay',
    #'x264',
}

GST_RTSP_SERVER_MESON_OPTIONS = {
    'rtspclientsink',
}

class PackageConan(ConanFile):
    name = "gstreamer-full"
    description = "GStreamer multimedia framework: full set of plugins and libraries"
    license = "LGPL-2.1-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/gstreamer/gstreamer"
    topics = ("audio", "multimedia", "streaming", "video")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "with_base": [True, False],
        "with_good": [True, False],
        "with_ugly": [True, False],
        "with_bad": [True, False],
        "with_libav": [True, False],
        "with_rtsp_server": [True, False],

        "with_orc": [True, False],
        "with_introspection": [True, False],
        "with_coretracers": [True, False],

        "with_tools": [True, False],

        "gst_base_audioresample_format": ["auto", "int", "float"],
        "gst_base_gl_jpeg": ["disabled", "libjpeg", "libjpeg-turbo"],

        # conan center packages / system
        "with_egl": [True, False],
        "with_wayland": [True, False],
        "with_xorg": [True, False],
    }
    options.update({f'gst_base_{_name}': [True, False] for _name in GST_BASE_MESON_OPTIONS})
    options.update({f'gst_base_{_name}': [True, False] for _name in GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS})
    options.update({f'gst_base_{_name}': [True, False] for _name in GST_BASE_MESON_OPTIONS_GL})
    options.update({f'gst_good_{_name}': [True, False] for _name in GST_GOOD_MESON_OPTIONS})
    options.update({f'gst_good_{_name}': [True, False] for _name in GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS})
    options.update({f'gst_bad_{_name}': [True, False] for _name in GST_BAD_MESON_OPTIONS})
    options.update({f'gst_bad_{_name}': [True, False] for _name in GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS})
    options.update({f'gst_ugly_{_name}': [True, False] for _name in GST_UGLY_MESON_OPTIONS})
    options.update({f'gst_ugly_{_name}': [True, False] for _name in GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS})
    options.update({f'gst_rtsp_server_{_name}': [True, False] for _name in GST_RTSP_SERVER_MESON_OPTIONS})

    default_options = {
        "shared": False,
        "with_base": True,
        "with_good": True,
        "with_ugly": True,
        "with_bad": True,
        "with_libav": True,
        "with_rtsp_server": True,

        "with_orc": True,
        "with_introspection": False, # 1.72 is not yet compatible with conan 2.0
        "with_coretracers": True,

        "with_tools": True, # Fails on windows due to LNK1170: line in command file contains maximum-length or more characters

        "gst_base_audioresample_format": "auto",
        "gst_base_gl_jpeg": "libjpeg",

        "with_egl": True,
        "with_wayland": True,
        "with_xorg": True,
    }
    default_options.update({f'gst_base_{_name}': True for _name in GST_BASE_MESON_OPTIONS})
    default_options.update({f'gst_base_{_name}': True for _name in GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS})
    default_options.update({f'gst_base_{_name}': True for _name in GST_BASE_MESON_OPTIONS_GL})
    default_options.update({f'gst_good_{_name}': True for _name in GST_GOOD_MESON_OPTIONS})
    default_options.update({f'gst_good_{_name}': True for _name in GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS})
    default_options.update({f'gst_bad_{_name}': True for _name in GST_BAD_MESON_OPTIONS})
    default_options.update({f'gst_bad_{_name}': True for _name in GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS})
    default_options.update({f'gst_ugly_{_name}': True for _name in GST_UGLY_MESON_OPTIONS})
    default_options.update({f'gst_ugly_{_name}': True for _name in GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS})
    default_options.update({f'gst_rtsp_server_{_name}': True for _name in GST_RTSP_SERVER_MESON_OPTIONS})

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os != "Linux":
            del self.options.with_wayland
            del self.options.gst_base_alsa
            del self.options.gst_base_x11
            del self.options.gst_base_xvideo
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.gst_bad_unixfd
            del self.options.gst_base_drm
            del self.options.with_egl
            del self.options.with_xorg

        if self.settings.os == "Windows": # TODO fix with_orc on windows
            del self.options.with_orc

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

        if not self.options.get_safe("with_xorg"):
            self.options.rm_safe('gst_base_x11')
            self.options.rm_safe('gst_base_xshm')
            self.options.rm_safe('gst_base_xi')
            self.options.rm_safe('gst_base_ximage')
            self.options.rm_safe('gst_base_xvimage')

        if not self.options.with_base:
            for option in GST_BASE_MESON_OPTIONS:
                delattr(self.options, f'gst_base_{option}')
            for option in GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS:
                delattr(self.options, f'gst_base_{option}')
            for option in GST_BASE_MESON_OPTIONS_GL:
                delattr(self.options, f'gst_base_{option}')
            delattr(self.options, "gst_base_gl_jpeg")
        if not self.options.with_good:
            for option in GST_GOOD_MESON_OPTIONS:
                delattr(self.options, f'gst_good_{option}')
            for option in GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS:
                delattr(self.options, f'gst_good_{option}')
        if not self.options.with_bad:
            for option in GST_BAD_MESON_OPTIONS:
                if option in self.options:
                    delattr(self.options, f'gst_bad_{option}')
            for option in GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS:
                delattr(self.options, f'gst_bad_{option}')
        if not self.options.with_ugly:
            for option in GST_UGLY_MESON_OPTIONS:
                delattr(self.options, f'gst_ugly_{option}')
            for option in GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS:
                delattr(self.options, f'gst_ugly_{option}')
        if not self.options.with_rtsp_server:
            for option in GST_RTSP_SERVER_MESON_OPTIONS:
                delattr(self.options, f'gst_rtsp_server_{option}')

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("glib/2.78.3", transitive_headers=True, transitive_libs=True)

        if self.options.with_base:
            self.requires("zlib/1.3.1", transitive_headers=True, transitive_libs=True)
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.requires("libdrm/2.4.120", transitive_headers=True, transitive_libs=True)

        if self.options.with_libav:
            self.requires("ffmpeg/6.1", transitive_headers=True, transitive_libs=True)

        if self.options.get_safe("gst_base_alsa"):
            self.requires("libalsa/1.2.10")
        if self.options.get_safe("gst_base_ogg"):
            self.requires("ogg/1.3.5")
        if self.options.get_safe("gst_base_opus"):
            self.requires("opus/1.4")
        if self.options.get_safe("gst_base_pango"):
            self.requires("pango/1.51.0")
        if self.options.get_safe("gst_base_theora"):
            self.requires("theora/1.1.1")
        if self.options.get_safe("gst_base_vorbis"):
            self.requires("vorbis/1.3.7")
        if self.options.get_safe("with_xorg"):
            self.requires("xorg/system")

        if self.options.get_safe("gst_base_gl"):
            self.requires("opengl/system")
            if self.settings.os == "Windows":
                self.requires("wglext/cci.20200813")
                self.requires('glext/cci.20210420')
            if self.options.get_safe("with_egl"):
                self.requires("egl/system")
            if self.options.get_safe("with_wayland"):
                self.requires("wayland/1.20.0")
                self.requires("wayland-protocols/1.33")
            if self.options.get_safe("gst_base_gl_graphene"):
                self.requires("graphene/1.10.8")
            if self.options.get_safe("gst_base_gl_png"):
                self.requires("libpng/1.6.43")
            if self.options.get_safe("gst_base_gl_jpeg") == "libjpeg":
                self.requires("libjpeg/9e")
            elif self.options.get_safe("gst_base_gl_jpeg") == "libjpeg-turbo":
                self.requires("libjpeg-turbo/3.0.2")

        if self.options.get_safe("gst_good_bz2"):
            self.requires("bzip2/1.0.8")
        if self.options.get_safe("gst_good_flac"):
            self.requires("flac/1.4.3")
        if self.options.get_safe("gst_good_gdk-pixbuf"):
            self.requires("gdk-pixbuf/2.42.10")
        if self.options.get_safe("gst_good_lame"):
            self.requires("libmp3lame/3.100")
        if self.options.get_safe("gst_good_mpg123"):
            self.requires("mpg123/1.31.2")
        if self.options.get_safe("gst_good_taglib"):
            self.requires("taglib/2.0")
        if self.options.get_safe("gst_good_vpx"):
            self.requires("libvpx/1.14.1")

    def validate(self):
        # TODO validate if still the case
        if self.dependencies.direct_host["glib"].options.shared and not self.options.shared:
            raise ConanInvalidConfiguration("static GStreamer cannot link to shared GLib")
        
        if not self.dependencies.direct_host["glib"].options.shared and self.options.shared:
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("shared GStreamer cannot link to static GLib")

        # Need rework, do we even need this???
        #if not self.options.get_safe("gst_base_gl") and (self.options.get_safe("gst_base_gl_graphene") or self.options.get_safe("gst_base_gl_jpeg") != "disabled" or self.options.get_safe("gst_base_gl_png")):
        #    raise ConanInvalidConfiguration("gst_base_gl_graphene, gst_base_gl_jpeg and gst_base_gl_png require gst_base_gl")

        if not self.options.with_base and self.options.with_libav:
            raise ConanInvalidConfiguration("libav is only available with base")

        self._validate_gl_config()

    def build_requirements(self):
        self.tool_requires("meson/1.3.1")
        self.tool_requires("glib/<host_version>") # we need glib-mkenums

        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/2.1.0")

        if self.settings.os == "Windows":
            self.tool_requires("winflexbison/2.5.25")
        else:
            self.tool_requires("bison/3.8.2")
            self.tool_requires("flex/2.6.4")

        if self.options.with_introspection:
            self.tool_requires("gobject-introspection/1.72.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _get_gl_api(self):
        gl_api = set()
        if self.options.get_safe("with_egl") or \
           self.options.get_safe("with_xorg") or \
           self.options.get_safe("with_wayland") or \
           self.settings.os == "Macos" or \
           self.settings.os == "Windows":
            gl_api.add("opengl")
        elif self.settings.os in ["iOS", "tvOS", "watchOS"]:
            gl_api.add("gles2")

        if len(gl_api) == 0:
            raise ConanInvalidConfiguration("No GL API selected")

        return list(gl_api)

    def _get_gl_platform(self):
        gl_platform = set()
        if self.options.get_safe("with_egl"):
            gl_platform.add("egl")
        if self.options.get_safe("with_xorg"):
            gl_platform.add("glx")
        if self.options.get_safe("with_wayland"):
            gl_platform.add("egl")
        if self.settings.os == "Macos":
            gl_platform.add("cgl")
        elif self.settings.os in ["iOS", "tvOS", "watchOS"]:
            gl_platform.add("eagl")
        elif self.settings.os == "Windows":
            gl_platform.add("wgl")

        return list(gl_platform)

    def _get_gl_winsys(self):
        gl_winsys = set()
        if self.options.get_safe("with_egl"):
            gl_winsys.add("egl")
        if self.options.get_safe("with_xorg"):
            gl_winsys.add("x11")
        if self.options.get_safe("with_wayland"):
            gl_winsys.add("wayland")
        if self.settings.os == "Macos":
            gl_winsys.add("cocoa")
        elif self.settings.os == "Windows":
            gl_winsys.add("win32")

        return list(gl_winsys)

    def _get_gl_platform_deps(self):
        gl_platform_deps = set()
        if self.options.get_safe("with_egl"):
            gl_platform_deps.add("egl::egl")

        return list(gl_platform_deps)

    def _get_gl_winsys_deps(self):
        gl_winsys_deps = set()
        if self.options.get_safe("with_xorg"):
            gl_winsys_deps.add("xorg::x11")
            gl_winsys_deps.add("xorg::x11-xcb")
        if self.options.get_safe("with_wayland"):
            gl_winsys_deps.add("wayland::wayland")
            gl_winsys_deps.add("wayland::wayland-client")
            gl_winsys_deps.add("wayland::wayland-cursor")
            gl_winsys_deps.add("wayland::wayland-egl")
            gl_winsys_deps.add("wayland-protocols::wayland-protocols")
        if self.settings.os == "Windows":
            gl_winsys_deps.add("wglext::wglext")
            gl_winsys_deps.add("glext::glext")

        return list(gl_winsys_deps)

    def _get_gl_system_deps(self):
        if self.settings.os == "Windows":
            return ["gdi32"]
        else:
            return []

    def _get_gl_plugin_deps(self):
        gl_plugin_deps = set()
        if self.options.get_safe("gst_base_gl_graphene"):
            gl_plugin_deps.add("graphene::graphene")
        if self.options.get_safe("gst_base_gl_png"):
            gl_plugin_deps.add("libpng::libpng")
        if self.options.get_safe("gst_base_gl_jpeg") == "libjpeg":
            gl_plugin_deps.add("libjpeg::libjpeg")
        elif self.options.get_safe("gst_base_gl_jpeg") == "libjpeg-turbo":
            gl_plugin_deps.add("libjpeg-turbo::libjpeg-turbo")

        if self.options.get_safe("with_xorg"):
            gl_plugin_deps.add("xorg::x11")

        return list(gl_plugin_deps)

    def _validate_gl_config(self):
        if self.options.get_safe("with_egl") and not self.options.get_safe("with_xorg"):
            raise ConanInvalidConfiguration("with_egl requires with_xorg")
        if self.options.get_safe("with_wayland") and not self.options.get_safe("with_egl"):
            raise ConanInvalidConfiguration("with_wayland requires with_egl")

    def generate(self):
        virtual_build_env = VirtualBuildEnv(self)
        virtual_build_env.generate()

        pkg_config_deps = PkgConfigDeps(self)
        pkg_config_deps.generate()

        tc = MesonToolchain(self)
        tc.project_options["auto_features"] = "disabled"

        if not self.options.shared:
            tc.project_options["default_library"] = "static" # gstreamer-full is only in static
            tc.project_options["gst-full"] = "enabled"
            tc.project_options["gst-full-target-type"] = "static_library"

        # GStreamer subprojects
        tc.project_options["base"] = "enabled" if self.options.with_base else "disabled"
        tc.project_options["good"] = "enabled" if self.options.with_good else "disabled"
        tc.project_options["ugly"] = "enabled" if self.options.with_ugly else "disabled"
        tc.project_options["bad"] = "enabled" if self.options.with_bad else "disabled"
        tc.project_options["libav"] = "enabled" if self.options.with_libav else "disabled"
        tc.project_options["rtsp_server"] = "enabled" if self.options.with_rtsp_server else "disabled"

        # Other options
        tc.project_options["build-tools-source"] = "system" # Use conan's flex and bison
        tc.project_options["orc-source"] = "subproject" # Conan doesn't provide orc

        # Common options
        tc.project_options["introspection"] = "enabled" if self.options.with_introspection else "disabled"
        tc.project_options["orc"] = "enabled" if self.options.get_safe('with_orc') else "disabled"

        tc.project_options["tools"] = "enabled" if self.options.with_tools else "disabled"

        if self.settings.compiler == "msvc":
            tc.project_options["c_args"] = "-%s" % self.settings.compiler.runtime
            tc.project_options["cpp_args"] = "-%s" % self.settings.compiler.runtime
            tc.project_options["c_link_args"] = "-lws2_32"
            tc.project_options["cpp_link_args"] = "-lws2_32"
            if int(str(self.settings.compiler.version)) < 14:
                    tc.project_options["c_args"].append(" -Dsnprintf=_snprintf")
                    tc.project_options["cpp_args"].append(" -Dsnprintf=_snprintf")

        if self.settings.get_safe("compiler.runtime"):
            tc.project_options["b_vscrt"] = str(self.settings.compiler.runtime).lower()

        # Enable all plugins by default
        tc.project_options["gst-full-plugins"] = '*'

        tc.subproject_options["gstreamer"] = [{'coretracers': 'enabled' if self.options.with_coretracers else 'disabled'}]

        # Feature options for plugins with no external deps
        if self.options.with_base:
            tc.subproject_options["gst-plugins-base"] = []
            for option in GST_BASE_MESON_OPTIONS:
                tc.subproject_options["gst-plugins-base"].append({option: 'enabled' if self.options.get_safe(f'gst_base_{option}') else 'disabled'})
            for option in GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS:
                tc.subproject_options["gst-plugins-base"].append({option: 'enabled' if self.options.get_safe(f'gst_base_{option}') else 'disabled'})

            tc.subproject_options["gst-plugins-base"].append({'audioresample_format': str(self.options.gst_base_audioresample_format)})
            if self.options.gst_base_gl:
                for option in GST_BASE_MESON_OPTIONS_GL:
                    mod_option = option.replace("gl_", "gl-")
                    tc.subproject_options["gst-plugins-base"].append({mod_option: 'enabled' if self.options.get_safe(f'gst_base_{option}') else 'disabled'})
                if self.options.gst_base_gl_jpeg != "disabled":
                    tc.subproject_options["gst-plugins-base"].append({'gl-jpeg': 'enabled'})

                tc.subproject_options["gst-plugins-base"].append({'gl_api': self._get_gl_api()})
                tc.subproject_options["gst-plugins-base"].append({'gl_platform': self._get_gl_platform()})
                tc.subproject_options["gst-plugins-base"].append({'gl_winsys': self._get_gl_winsys()})

        if self.options.with_good:
            tc.subproject_options["gst-plugins-good"] = []
            for option in GST_GOOD_MESON_OPTIONS:
                tc.subproject_options["gst-plugins-good"].append({option: 'enabled' if self.options.get_safe(f'gst_good_{option}') else 'disabled'})
            for option in GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS:
                tc.subproject_options["gst-plugins-good"].append({option: 'enabled' if self.options.get_safe(f'gst_good_{option}') else 'disabled'})

        if self.options.with_bad:
            tc.subproject_options["gst-plugins-bad"] = []
            for option in GST_BAD_MESON_OPTIONS:
                tc.subproject_options["gst-plugins-bad"].append({option: 'enabled' if self.options.get_safe(f'gst_bad_{option}') else 'disabled'})
            for option in GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS:
                tc.subproject_options["gst-plugins-bad"].append({option: 'enabled' if self.options.get_safe(f'gst_bad_{option}') else 'disabled'})

        if self.options.with_ugly:
            tc.subproject_options["gst-plugins-ugly"] = []
            for option in GST_UGLY_MESON_OPTIONS:
                tc.subproject_options["gst-plugins-ugly"].append({option: 'enabled' if self.options.get_safe(f'gst_ugly_{option}') else 'disabled'})
            for option in GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS:
                tc.subproject_options["gst-plugins-ugly"].append({option: 'enabled' if self.options.get_safe(f'gst_ugly_{option}') else 'disabled'})

        if self.options.with_rtsp_server:
            tc.subproject_options["gst-rtsp-server"] = []
            for option in GST_RTSP_SERVER_MESON_OPTIONS:
                tc.subproject_options["gst-rtsp-server"].append({option: 'enabled' if self.options.get_safe(f'gst_rtsp_server_{option}') else 'disabled'})

        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        meson = Meson(self)
        meson.configure()
        meson.build()

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "msvc":
            with chdir(self, path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()

        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "gstreamer-1.0", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))

    def _add_plugin_components(self, lib, requires = [], system_libs = []):
        self.cpp_info.components[f"gst{lib}"].libs = [f"gst{lib}"]
        self.cpp_info.components[f"gst{lib}"].libdirs = [os.path.join(self.package_folder, "lib", "gstreamer-1.0")]
        self.cpp_info.components[f"gst{lib}"].requires = requires
        self.cpp_info.components[f"gst{lib}"].system_libs = system_libs
        if not self.options.shared:
            self.cpp_info.components[f"gst{lib}"].defines = ["GST_STATIC_COMPILATION"]
        self.libraries.append(f"gst{lib}")

    def _add_library_components(self, lib, requires = [], system_libs = []):
        self.cpp_info.components[f"gstreamer-{lib}-1.0"].libs = [f"gst{lib}-1.0"]
        self.cpp_info.components[f"gstreamer-{lib}-1.0"].libdirs = [os.path.join(self.package_folder, "lib")]
        self.cpp_info.components[f"gstreamer-{lib}-1.0"].includedirs = [os.path.join(self.package_folder, "include", "gstreamer-1.0")]
        self.cpp_info.components[f"gstreamer-{lib}-1.0"].requires = requires
        self.cpp_info.components[f"gstreamer-{lib}-1.0"].system_libs = system_libs
        if not self.options.shared:
            self.cpp_info.components[f"gstreamer-{lib}-1.0"].defines = ["GST_STATIC_COMPILATION"]
        return [f"gstreamer-{lib}-1.0"]

    def _add_plugin_components_loop(self, options_list, conan_option_prefix, plugin_list):
        for lib in options_list:
            if self.options.get_safe(f'{conan_option_prefix}_{lib}'):
                for plugin in plugin_list[lib]:
                    requires = []
                    system_requires = []

                    for require in plugin[1:]:
                        if require is None or require == []:
                            continue
                        if require[0] in self._system_libs:
                            system_requires.extend(require)
                        else:
                            requires.extend(require)

                    self._add_plugin_components(plugin[0], requires, system_requires)

    def package_info(self):
        if self.options.get_safe('with_orc'):
            orc_dep = ["orc"]
            self.cpp_info.components["orc"].libs = ["orc-0.4"]
            self.cpp_info.components["orc"].includedirs = [os.path.join(self.package_folder, "include", "orc-0.4")]
            self.cpp_info.components["orc"].set_property("cmake_target_name", "orc")
        else:
            orc_dep = []

        self.libraries = []
        self.cpp_info.components["gstreamer-1.0"].libs = ["gstreamer-1.0"]
        self.cpp_info.components["gstreamer-1.0"].libdirs = [os.path.join(self.package_folder, "lib")]
        self.cpp_info.components["gstreamer-1.0"].includedirs = [os.path.join(self.package_folder, "include", "gstreamer-1.0")]
        self.cpp_info.components["gstreamer-1.0"].requires = ["glib::glib-2.0", "glib::gobject-2.0", "glib::gmodule-2.0"]
        if not self.options.shared:
            self.cpp_info.components["gstreamer-1.0"].defines = ["GST_STATIC_COMPILATION"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["gstreamer-1.0"].system_libs.extend(["m", "pthread"])
        elif self.settings.os == "Windows":
            self.cpp_info.components["gstreamer-1.0"].system_libs.append("ws2_32")
        elif self.settings.os == "Macos":
            self.cpp_info.components["gstreamer-1.0"].system_libs.append("Cocoa")
        elif self.settings.os == "Android":
            self.cpp_info.components["gstreamer-1.0"].system_libs.append("log")

        bz2_dep = ["bzip2::bzip2"] if self.options.get_safe("gst_good_bz2") else []
        cocoa = ["Cocoa"] if self.settings.os == "Macos" else []
        flac_dep = ["flac::flac"] if self.options.get_safe("gst_good_flac") else []
        gdkpixbuf_dep = ["gdk-pixbuf::gdk-pixbuf"] if self.options.get_safe("gst_good_gdk-pixbuf") else []
        gio_dep = ["glib::gio-2.0"]
        gio_unix_dep = ["glib::gio-unix-2.0"]
        gmodule_dep = ["glib::gmodule-2.0"]
        lame_dep = ["libmp3lame::libmp3lame"] if self.options.get_safe("gst_good_lame") else []
        libdrm_dep = ["libdrm::libdrm"] if self.settings.os in ["Linux"] else []
        libm = ["m"] if self.settings.os in ["Linux", "FreeBSD"] else []
        log = ["log"] if self.settings.os == "Android" else []
        mpg123_dep = ["mpg123::libmpg123"] if self.options.get_safe("gst_good_mpg123") else []
        network_deps = [] # TODO: Probably required for Solaris
        taglib_dep = ["taglib::taglib"] if self.options.get_safe("gst_good_taglib") else []
        thread_dep = ["pthread"] if self.settings.os in ["Linux", "FreeBSD"] else []
        vpx_dep = ["libvpx::libvpx"] if self.options.get_safe("gst_good_vpx") else []
        winsock2 = ["ws2_32"] if self.settings.os == "Windows" else []
        wl_client_dep = ["wayland-client"] if self.settings.os == "Linux" else []
        x11_dep = []
        x264_dep = ["libx264::libx264"]
        xi_dep = []
        xshm_dep = []
        xvideo_dep = []
        zlib_dep = ["zlib::zlib"]

        # List of libs that need to be in system_requires rather than requires
        # TODO cocoa seems to belong to framework rather than system_requires
        self._system_libs = libm + winsock2 + cocoa + log + thread_dep

        gst_dep = ["gstreamer-1.0"]
        # Gstreamer uses gstbase_dep and gst_base_dep interchangeably
        gstbase_dep = self._add_library_components("base", gst_dep)
        gst_base_dep = self._add_library_components("base", gst_dep)
        gstcontroller_dep = self._add_library_components("controller", gst_dep, libm)
        gstnet_dep = self._add_library_components("net", gst_dep, libm)

        if self.options.with_base:
            gstallocators_dep = self._add_library_components("allocators", libdrm_dep + gst_dep)
            gstapp_dep = self._add_library_components("app", gstbase_dep)
            gsttag_dep = self._add_library_components("tag", gstbase_dep + zlib_dep, libm)
            gstaudio_dep = self._add_library_components("audio", gsttag_dep + gstbase_dep + gst_dep + orc_dep, libm)
            gstvideo_dep = self._add_library_components("video", gstbase_dep + orc_dep, libm)
            gstfft_dep = self._add_library_components("fft", gst_dep, libm)
            gstriff_dep = self._add_library_components("riff", gstaudio_dep + gsttag_dep)
            gstrtp_dep = self._add_library_components("rtp", gstaudio_dep + gstbase_dep)
            gstpbutils_dep = self._add_library_components("pbutils", gstvideo_dep + gstaudio_dep + gsttag_dep)
            gstsdp_dep = self._add_library_components("sdp", gstrtp_dep + gst_dep + gio_dep + gstpbutils_dep)
            gstrtsp_dep = self._add_library_components("rtsp", gstbase_dep + gst_dep + gio_dep + gstsdp_dep, libm + winsock2)

            gsttypefindfunctions_dep = []
            if self.options.get_safe('gst_base_typefind') and self.options.get_safe('gst_base_gio-typefinder'):
                gsttypefindfunctions_dep.extend(["glib::gio-2.0"])

            if self.options.get_safe('gst_base_x11'):
                x11_dep = ["xorg::x11"]
                xvideo_dep = ["xorg::xv"]
                if self.options.get_safe('gst_base_xshm'):
                    xshm_dep = ["xorg::xext"]
                if self.options.get_safe('gst_base_xi'):
                    xi_dep = ["xorg::xi"]

            gstgl_dep = []
            gl_lib_deps = ["opengl::opengl"]
            gl_misc_deps = []

            if getattr(self.options, 'gst_base_gl'):
                gstgl_dep = self._add_library_components("gl", gstbase_dep + gstvideo_dep + gstallocators_dep + gmodule_dep + gl_lib_deps + self._get_gl_platform_deps() + self._get_gl_winsys_deps() + gl_misc_deps);
                #self._add_library_components("gl-prototypes", gstgl_dep + gl_lib_deps)

#                if self.options.get_safe("with_xorg"):
#                    self._add_library_components("gl-x11", gstgl_dep, ["xorg::x11", "xorg::x11-xcb"])
#
#                if self.options.get_safe("with_wayland"):
#                    self._add_library_components("gl-wayland", gstgl_dep)
#
#                if self.options.get_safe("with_egl"):
#                    self._add_library_components("gl-egl", gstgl_dep)

            # Example: subprojects/gst-plugins-base/gst/app/meson.build
            ####################################################################
            # app_sources = [
            #   'gstapp.c',
            #   'gstappsink.c',
            #   'gstappsrc.c',
            # ]
            # 
            # gstapp_plugin = library('gstapp',
            #   app_sources,
            #   c_args: gst_plugins_base_args,
            #   include_directories: [configinc],
            #   dependencies : [gst_base_dep, app_dep, tag_dep],
            #   install : true,
            #   install_dir : plugins_install_dir,
            # )
            # 
            # plugins += [gstapp_plugin]
            ####################################################################
            # app plugin names comes from meson_options.txt
            # app plugin library comes from line library('gstapp'
            # Dependencies are as listed
            # base_plugins format is (plugin_name, [dependencies])
            # this was chosen to make it easier to add new plugins
            # and to copy the meson.build format of dependencies.

            # drm doesn't genereate a lib, it adds a dummy drm driver in gstreamer-allocators
            # gio-typefind is to add glib2::gio-2.0 to typefindfunctions
            # xi and xshm doesn't generate a lib
            base_plugins = {
                "adder": [("adder", gstaudio_dep, orc_dep)],
                "app": [("app", gstbase_dep, gstapp_dep, gsttag_dep)],
                "audioconvert": [("audioconvert", gstaudio_dep, gstbase_dep)],
                "audiomixer": [("audiomixer", gstaudio_dep, gstbase_dep, orc_dep)],
                "audiorate": [("audiorate", gstaudio_dep, gstbase_dep)],
                "audioresample": [("audioresample", gstaudio_dep, gstbase_dep)],
                "audiotestsrc": [("audiotestsrc", gstaudio_dep, gstbase_dep)],
                "compositor": [("compositor", gstvideo_dep, gstbase_dep, orc_dep)],
                "debugutils": [("basedebug", gst_dep, gstbase_dep, gstvideo_dep)],
                "drm": [],
                "dsd": [("dsd", gstaudio_dep, gstbase_dep)],
                "encoding": [("encoding", gstpbutils_dep, gstvideo_dep, gstbase_dep)],
                "gio": [("gio", gstbase_dep, gio_dep)],
                "gio-typefinder": [],
                "overlaycomposition": [("overlaycomposition", gstvideo_dep)],
                "pbtypes": [("pbtypes", gstvideo_dep)],
                "playback": [("playback", gstaudio_dep, gstvideo_dep, gstpbutils_dep, gsttag_dep)],
                "rawparse": [("rawparse", gstbase_dep, gstvideo_dep, gstaudio_dep)],
                "subparse": [("subparse", gstbase_dep)],
                "tcp": [("tcp", gstbase_dep, gstnet_dep, gio_dep)],
                "typefind": [("typefindfunctions", gstpbutils_dep, gstbase_dep, gsttypefindfunctions_dep)],
                "videoconvertscale": [("videoconvertscale", gstvideo_dep, gst_dep, gstbase_dep)],
                "videorate": [("videorate", gstvideo_dep)],
                "videotestsrc": [("videotestsrc", gstvideo_dep, gst_dep, gstbase_dep, orc_dep)],
                "volume": [("volume", gstaudio_dep, gst_dep, gstbase_dep, orc_dep)],

                # External dependencies
                "alsa": [("alsa", ["libalsa::libalsa"], gstaudio_dep, gsttag_dep, gst_dep, gstbase_dep)],
                "ogg": [("ogg", ["ogg::ogg"], gstaudio_dep, gstpbutils_dep, gsttag_dep, gstriff_dep, gst_dep, gstbase_dep)],
                "opus": [("opus", ["opus::opus"], gstpbutils_dep, gsttag_dep, gstaudio_dep, gst_dep, gstbase_dep, libm)],
                "pango": [("pango", ["pango::pangocairo"], gstvideo_dep, gst_dep, gstbase_dep, libm)],
                "theora": [("theora", ["theora::theora"], gstvideo_dep, gsttag_dep, gst_dep, gstbase_dep)],
                #"tremor": [("tremor", ["tremor::tremor"], gstaudio_dep, gstpbutils_dep, gsttag_dep, gstriff_dep, gst_dep, gstbase_dep)],
                "vorbis": [("vorbis", ["vorbis::vorbis"], gstaudio_dep, gstpbutils_dep, gsttag_dep, gstriff_dep, gst_dep, gstbase_dep)],
                "x11": [("ximagesink", gstvideo_dep, gst_dep, gstbase_dep)],
                "xshm": [],
                "xvideo": [("xvimagesink", gst_base_dep, gst_dep, x11_dep, xshm_dep, xvideo_dep, xi_dep, libm)],
                "xi": [],

                # GL
                "gl": [("opengl", gstgl_dep, gstvideo_dep, gstbase_dep, gstcontroller_dep, gl_lib_deps, self._get_gl_plugin_deps(), libm)],
                "gl_graphene": [],
                "gl_png": [],
            }

            base_options = GST_BASE_MESON_OPTIONS.union(GST_BASE_MESON_OPTIONS_WITH_EXT_DEPS).union(GST_BASE_MESON_OPTIONS_GL)
            self._add_plugin_components_loop(base_options, 'gst_base', base_plugins)

        if self.options.with_good:
            good_plugins = {
                "alpha": [
                    ("alpha", gstvideo_dep, gst_dep, libm),
                    ("alphacolor", gstvideo_dep, gst_dep)
                ],
                "apetag": [("apetag", gstpbutils_dep, gsttag_dep, gst_dep)],
                "audiofx": [("audiofx", orc_dep, gstaudio_dep, gstfft_dep, libm)],
                "audioparsers": [("audioparsers", gst_dep, gstbase_dep, gstpbutils_dep, gstaudio_dep, gsttag_dep)],
                "auparse": [("auparse", gstaudio_dep, gstbase_dep)],
                "autodetect": [("autodetect", gst_dep)],
                "avi": [("avi", gst_dep, gstriff_dep, gstaudio_dep, gstvideo_dep, gsttag_dep)],
                "cutter": [("cutter", gstbase_dep, gstaudio_dep, libm)],
                "debugutils": [
                    ("navigationtest", gstbase_dep, gstvideo_dep, libm),
                    ("debug", gst_dep, gstbase_dep, gstvideo_dep)
                ],
                "deinterlace": [("deinterlace", orc_dep, gstbase_dep, gstvideo_dep)],
                "dtmf": [("dtmf", gstbase_dep, gstrtp_dep, libm)],
                "effectv": [("effectv", gst_dep, gstbase_dep, gstvideo_dep, libm)],
                "equalizer": [("equalizer", gstbase_dep, gstaudio_dep, libm)],
                "flv": [("flv", gstpbutils_dep, gstvideo_dep, gsttag_dep, gstaudio_dep)],
                "flx": [("flxdec", gstbase_dep, gstvideo_dep, gst_dep)],
                "goom": [("goom", gst_dep, gstpbutils_dep, gstbase_dep, orc_dep, libm)],
                "goom2k1": [("goom2k1", gstpbutils_dep, gstbase_dep, libm)],
                "icydemux": [("icydemux", gst_dep, gstbase_dep, gsttag_dep, zlib_dep)],
                "id3demux": [("id3demux", gst_dep, gstbase_dep, gsttag_dep, gstpbutils_dep)],
                "imagefreeze": [("imagefreeze", gst_dep)],
                "interleave": [("interleave", gstbase_dep, gstaudio_dep)],
                "isomp4": [("isomp4", gst_dep, gstriff_dep, gstaudio_dep, gstvideo_dep, gstrtp_dep, gsttag_dep, gstpbutils_dep, zlib_dep)],
                "law": [
                    ("alaw", gstbase_dep, gstaudio_dep),
                    ("mulaw", gstbase_dep, gstaudio_dep)
                ],
                "level": [("level", gstbase_dep, gstaudio_dep, libm)],
                "matroska": [("matroska", gstpbutils_dep, gstaudio_dep, gstriff_dep, gstvideo_dep, gsttag_dep, gstbase_dep, gst_dep, zlib_dep, bz2_dep, libm)],
                "monoscope": [("monoscope", gstbase_dep, gstaudio_dep, gstvideo_dep)],
                "multifile": [("multifile", gstvideo_dep, gstbase_dep, gstpbutils_dep, gio_dep)],
                "multipart": [("multipart", gstbase_dep)],
                "replaygain": [("replaygain", gst_dep, gstbase_dep, gstpbutils_dep, gstaudio_dep, libm)],
                "rtp": [("rtp", gstbase_dep, gstaudio_dep, gstvideo_dep, gsttag_dep, gstrtp_dep, gstpbutils_dep, libm)],
                "rtpmanager": [("rtpmanager", gstbase_dep, gstnet_dep, gstrtp_dep, gstaudio_dep, gio_dep)],
                "rtsp": [("rtsp", gstbase_dep, gstrtp_dep, gstrtsp_dep, gstsdp_dep, gstnet_dep, gio_dep)],
                "shapewipe": [("shapewipe", gst_dep, gstvideo_dep, gio_dep)],
                "smpte": [("smpte", gstvideo_dep, gst_dep, libm)],
                "spectrum": [("spectrum", gstbase_dep, gstfft_dep, gstaudio_dep, libm)],
                "udp": [("udp", gst_dep, gstbase_dep, gstnet_dep, gio_dep)],
                "videobox": [("videobox", orc_dep, gstbase_dep, gstvideo_dep)],
                "videocrop": [("videocrop", gst_dep, gstbase_dep, gstvideo_dep)],
                "videofilter": [("videofilter", gstbase_dep, gstvideo_dep, libm)],
                "videomixer": [("videomixer", orc_dep, gstvideo_dep, gstbase_dep, libm)],
                "wavenc": [("wavenc", gstbase_dep, gstaudio_dep, gstriff_dep)],
                "wavparse": [("wavparse", gstbase_dep, gstpbutils_dep, gstriff_dep, gstaudio_dep, gsttag_dep, libm)],
                "xingmux": [("xingmux", gstbase_dep)],
                "y4m": [("y4menc", gstbase_dep, gstvideo_dep)],

                # External dependencies
                #"adaptivedemux2",
                #"aalib",
                #"amrnb",
                #"amrwbdec",
                "bz2": [], # Doesn't build lib, only add bz2 support to matroska
                #"cairo",
                #"directsound",
                #"dv",
                #"dv1394",
                "flac": [("flac", gstbase_dep, gsttag_dep, gstaudio_dep, flac_dep)],
                "gdk-pixbuf": [("gdkpixbuf", gstbase_dep, gstvideo_dep, gstcontroller_dep, gdkpixbuf_dep)],
                #"gtk3",
                #"jack",
                #"jpeg",
                "lame": [("lame", gstaudio_dep, lame_dep)],
                #"libcaca",
                "mpg123": [("mpg123", gstaudio_dep, mpg123_dep)],
                #"oss",
                #"oss4",
                #"osxaudio",
                #"osxvideo",
                #"png",
                #"pulse",
                #"shout2",
                #"speex",
                "taglib": [("taglib", gsttag_dep, taglib_dep)],
                #"twolame",
                "vpx": [("vpx", gstbase_dep, gsttag_dep, gstvideo_dep, vpx_dep)],
                #"waveform",
                #"wavpack",
            }

            base_options = GST_GOOD_MESON_OPTIONS.union(GST_GOOD_MESON_OPTIONS_WITH_EXT_DEPS)
            self._add_plugin_components_loop(base_options, 'gst_good', good_plugins)

        if self.options.with_bad:
            gsturidownloader_dep = self._add_library_components("uridownloader", gstbase_dep)
            gstadaptivedemux_dep = self._add_library_components("adaptivedemux", gstbase_dep + gsturidownloader_dep)
            gstanalytics_dep = self._add_library_components("analytics", gstbase_dep + gstvideo_dep)
            gstbadaudio_dep = self._add_library_components("badaudio", gstbase_dep + gstaudio_dep)
            gstbasecamerabin_dep = self._add_library_components("basecamerabinsrc", gstapp_dep)
            gstcodecparsers_dep = self._add_library_components("codecparsers", gstbase_dep)
            gstcodecs_dep = self._add_library_components("codecs", gstvideo_dep + gstcodecparsers_dep)
            #gstcuda_dep = self._add_library_components("cuda", gstbase_dep + gmodule_dep + gstvideo_dep + gstglproto_dep + gstcuda_platform_dep)
            #gstd3d11_dep = self._add_library_components("d3d11", gstbase_dep + gstvideo_dep + d3d11_lib + dxgi_lib)
            if self.settings.os == "Windows":
                gstdxva_dep = self._add_library_components("dxva", gstvideo_dep + gstcodecs_dep)
            gstinsertbin_dep = self._add_library_components("insertbin", gst_dep)
            gstphotography_dep = self._add_library_components("photography", gst_dep)
            gstisoff_dep = self._add_library_components("isoff", gstbase_dep)
            gstmpegts_dep = self._add_library_components("mpegts", gst_dep)
            gstmse_dep = self._add_library_components("mse", gstbase_dep + gstapp_dep)
            #gstopencv_dep = self._add_library_components("opencv", gstbase_dep + gstvideo_dep + opencv_dep) TODO handle opencv dependency
            gstplay_dep = self._add_library_components("play", gstbase_dep + gstvideo_dep + gstaudio_dep + gsttag_dep + gstpbutils_dep)
            gstplayer_dep = self._add_library_components("player", gstbase_dep + gstvideo_dep + gstaudio_dep + gstplay_dep + gsttag_dep + gstpbutils_dep)
            gstsctp_dep = self._add_library_components("sctp", gstbase_dep)
            gst_transcoder_dep = self._add_library_components("transcoder", gst_dep + gstpbutils_dep)
            #gstva_dep = self._add_library_components("va", gst_dep + gstvideo_dep + gstallocators_dep + libva_dep + platform_deps)
            #TODO vulkan, multiple lib
            #gstwayland_dep = self._add_library_components("wayland", gst_dep + gstallocators_dep + gstvideo_dep + libdrm_dep, wl_client_dep)
            gstwebrtc_dep = self._add_library_components("webrtc", gstbase_dep + gstsdp_dep)
            #gstwinrt_dep = self._add_library_components("winrt", gstbase_dep + runtimeobject_lib)

            bad_plugins = {
                'accurip': [("accurip", gstbase_dep, gstaudio_dep)],
                'adpcmdec': [("adpcmdec", gstbase_dep, gstaudio_dep)],
                'adpcmenc': [("adpcmenc", gstbase_dep, gstaudio_dep)],
                'aiff': [("aiff", gstbase_dep, gsttag_dep, gstaudio_dep, gstpbutils_dep, libm)],
                #'analyticsoverlay: [("analyticsoverlay", )],
                'asfmux': [("asfmux", gstbase_dep, gstrtp_dep)],
                'audiobuffersplit': [("audiobuffersplit", gstbase_dep, gstaudio_dep)],
                'audiofxbad': [("audiofxbad", gstbase_dep, gstaudio_dep, libm)],
                'audiolatency': [("audiolatency", gstbase_dep)],
                'audiomixmatrix': [("audiomixmatrix", gstbase_dep, gstaudio_dep, libm)],
                'audiovisualizers': [("audiovisualizers", gstbase_dep, gstpbutils_dep, gstaudio_dep, gstvideo_dep, gstfft_dep, libm)],
                'autoconvert': [("autoconvert", gstbase_dep, gstpbutils_dep, gstvideo_dep)],
                'bayer': [("bayer", gstbase_dep, gstvideo_dep, orc_dep)],
                'camerabin2': [("camerabin", gstbasecamerabin_dep, gstphotography_dep, gsttag_dep, gstapp_dep, gstpbutils_dep, gstbase_dep)],
                'codecalpha': [("codecalpha", gstvideo_dep, gstpbutils_dep)],
                'codectimestamper': [("codectimestamper", gstcodecparsers_dep, gstbase_dep, gstvideo_dep)],
                'coloreffects': [("coloreffects", gstbase_dep, gstvideo_dep)],
                'debugutils': [("debugutilsbad", gstbase_dep, gstvideo_dep, gstnet_dep, gstaudio_dep, gio_dep)],
                'dvbsubenc': [("dvbsubenc", gstbase_dep, gstvideo_dep, libm)],
                'dvbsuboverlay': [("dvbsuboverlay", gstbase_dep, gstvideo_dep)],
                'dvdspu': [("dvdspu", gstbase_dep, gstvideo_dep)],
                'faceoverlay': [("faceoverlay", gstbase_dep, gstvideo_dep)],
                'festival': [("festival", gstbase_dep, gstaudio_dep, winsock2 + network_deps)],
                'fieldanalysis': [("fieldanalysis", gstbase_dep, gstvideo_dep, orc_dep)],
                'freeverb': [("freeverb", gstbase_dep, gstaudio_dep)],
                'frei0r': [("frei0r", gstbase_dep, gstvideo_dep, gmodule_dep)],
                'gaudieffects': [("gaudieffects", gstbase_dep, gstvideo_dep, orc_dep, libm)],
                'gdp': [("gdp", gstbase_dep)],
                'geometrictransform': [("geometrictransform", gstbase_dep, gstvideo_dep, libm)],
                'id3tag': [("id3tag", gstbase_dep, gsttag_dep)],
                'insertbin': [("insertbin", gst_dep, gstinsertbin_dep)],
                'inter': [("inter", gstaudio_dep, gstvideo_dep, gstbase_dep)],
                'interlace': [("interlace", gstbase_dep, gstvideo_dep)],
                'ivfparse': [("ivfparse", gstbase_dep)],
                'ivtc': [("ivtc", gstbase_dep, gstvideo_dep)],
                'jp2kdecimator': [("jp2kdecimator", gstbase_dep)],
                'jpegformat': [("jpegformat", gstbase_dep, gstcodecparsers_dep, gstvideo_dep, gsttag_dep)],
                #'librfb': [("librfb", gstbase_dep, gstvideo_dep, gio_dep, x11_dep)],
                'midi': [("midi", gstbase_dep, gsttag_dep, libm)],
                'mpegdemux': [("mpegpsdemux", gstbase_dep, gsttag_dep, gstpbutils_dep)],
                'mpegpsmux': [("mpegpsmux", gstbase_dep)],
                'mpegtsdemux': [("mpegtsdemux", gstcodecparsers_dep, gstmpegts_dep, gsttag_dep, gstpbutils_dep, gstaudio_dep, gstbase_dep, libm)],
                'mpegtsmux': [("mpegtsmux", gstmpegts_dep, gsttag_dep, gstpbutils_dep, gstaudio_dep, gstvideo_dep, gstbase_dep)],
                'mse': [("mse", gstbase_dep, gstmse_dep)],
                'mxf': [("mxf", gstbase_dep, gstaudio_dep, gstvideo_dep)],
                'netsim': [("netsim", gstbase_dep, libm)],
                'onvif': [("rtponvif", gstrtp_dep, gstbase_dep)],
                'pcapparse': [("pcapparse", gstbase_dep, winsock2)],
                'pnm': [("pnm", gstbase_dep, gstvideo_dep)],
                'proxy': [("proxy", gstbase_dep)],
                'rawparse': [("legacyrawparse", gstbase_dep, gstvideo_dep, gstaudio_dep)],
                'removesilence': [("removesilence", gstbase_dep, gstaudio_dep, libm)],
                'rist': [("rist", gstrtp_dep, gstnet_dep, gio_dep)],
                'rtmp2': [("rtmp2", gstbase_dep, gio_dep, libm)],
                'rtp': [("rtpmanagerbad", gst_dep, gstbase_dep, gstrtp_dep, gstnet_dep, gstcontroller_dep, gio_dep)],
                'sdp': [("sdpelem", gstbase_dep, gstrtp_dep, gstsdp_dep, gio_dep, gstapp_dep)],
                'segmentclip': [("segmentclip", gstbase_dep, gstaudio_dep, gstvideo_dep)],
                'siren': [("siren", gstbase_dep, gstaudio_dep, libm)],
                'smooth': [("smooth", gstbase_dep, gstvideo_dep)],
                'speed': [("speed", gstbase_dep, gstaudio_dep, libm)],
                'subenc': [("subenc", gstbase_dep)],
                'switchbin': [("switchbin", gst_dep)],
                'timecode': [("timecode", gstbase_dep, gstaudio_dep, gstvideo_dep)],
                'transcode': [("transcode", gst_dep, gstpbutils_dep)],
                'unixfd': [("unixfd", gstbase_dep, gstallocators_dep, gio_dep, gio_unix_dep)],
                'videofilters': [("videofiltersbad", gstvideo_dep, gstbase_dep, orc_dep, libm)],
                'videoframe_audiolevel': [("videoframe_audiolevel", gstvideo_dep, gstaudio_dep, libm)],
                'videoparsers': [("videoparsersbad", gstcodecparsers_dep, gstbase_dep, gstpbutils_dep, gstvideo_dep)],
                'videosignal': [("videosignal", gstbase_dep, gstvideo_dep)],
                'vmnc': [("vmnc", gstbase_dep, gstvideo_dep)],
                'y4m': [("y4mdec", gstbase_dep, gstvideo_dep)],

                # External dependencies
                #'aes',
                #'analyticsoverlay',
                #'assrender',
                #'aom',
                #'avtp',
                #'bs2b',
                #'bz2',
                #'chromaprint',
                #'closedcaption',
                #'codec2json',
                #'colormanagement',
                #'curl',
                #'dash',
                #'dc1394',
                #'directfb',
                #'dtls',
                #'dts',
                #'faac',
                #'faad',
                #'fdkaac',
                #'flite',
                #'fluidsynth',
                #'gme',
                #'gs',
                #'gsm',
                #'gtk',
                #'hls',
                #'iqa',
                #'isac',
                #'ladspa',
                #'lc3',
                #'ldac',
                #'libde265',
                #'lv2',
                #'mdns',
                #'modplug',
                #'mpeg2enc',
                #'mplex',
                #'musepack',
                #'neon',
                #'onnx',
                #'openal',
                #'openaptx',
                #'opencv',
                #'openexr',
                #'openh264',
                #'openjpeg',
                #'openmpt',
                #'openni2',
                #'opus',
                #'qroverlay',
                #'qt6d3d11',
                #'resindvd',
                #'rsvg',
                #'rtmp',
                #'sbc',
                #'sctp',
                #'smoothstreaming',
                #'sndfile',
                #'soundtouch',
                #'spandsp',
                #'srt',
                #'srtp',
                #'svtav1',
                #'svthevcenc',
                #'teletextdec',
                #'ttml',
                #'voaacenc',
                #'voamrwbenc',
                #'vulkan',
                #'wayland',
                #'webrtc',
                #'webrtcdsp',
                #'webp',
                #'wildmidi',
                #'wpe',
                #'x265',
                #'zxing',
                #'zbar',
            }

            bad_options = GST_BAD_MESON_OPTIONS.union(GST_BAD_MESON_OPTIONS_WITH_EXT_DEPS)
            self._add_plugin_components_loop(bad_options, 'gst_bad', bad_plugins)

        if self.options.with_ugly:
            ugly_plugins = {
                'asfdemux': [("asf", gstbase_dep, gstrtp_dep, gstvideo_dep, gstaudio_dep, gsttag_dep, gstriff_dep, gstrtsp_dep, gstsdp_dep)],
                'dvdlpcmdec': [("dvdlpcmdec", gstbase_dep, gstaudio_dep)],
                'dvdsub': [("dvdsub", gstbase_dep, gstvideo_dep)],
                'realmedia': [("realmedia", gstbase_dep, gstrtsp_dep, gstsdp_dep, gstpbutils_dep)],

                # External dependencies
                'x264': [("x264", gstbase_dep, x264_dep)],
            }

            ugly_options = GST_UGLY_MESON_OPTIONS.union(GST_UGLY_MESON_OPTIONS_WITH_EXT_DEPS)
            self._add_plugin_components_loop(ugly_options, 'gst_ugly', ugly_plugins)

        if self.options.with_libav:
            libav_deps = ["ffmpeg::avfilter", "ffmpeg::avformat", "ffmpeg::avcodec", "ffmpeg::avutil"]
            libav_deps.extend(gst_dep + gstaudio_dep + gstvideo_dep + gstbase_dep)
            self._add_plugin_components("libav", libav_deps)

        if self.options.with_rtsp_server:
            gst_rtsp_server_dep = self._add_library_components("rtspserver", gstrtsp_dep + gstrtp_dep + gstsdp_dep + gstnet_dep + gstapp_dep + gstvideo_dep)

            rtsp_server_plugins = {
                'rtspclientsink': [("rtspclientsink", gstrtsp_dep + gstsdp_dep + gst_rtsp_server_dep)]
            }

            self._add_plugin_components_loop(GST_RTSP_SERVER_MESON_OPTIONS, 'gst_rtsp_server', rtsp_server_plugins)

        self.cpp_info.components["gstcoreelements"].libs = ["gstcoreelements"]
        self.cpp_info.components["gstcoreelements"].libdirs = [os.path.join(self.package_folder, "lib", "gstreamer-1.0")]
        self.cpp_info.components["gstcoreelements"].includedirs = [os.path.join(self.package_folder, "include", "gstreamer-1.0")]
        self.cpp_info.components["gstcoreelements"].requires = gst_dep + gstbase_dep
        self.libraries.append("gstcoreelements")

        if self.options.with_coretracers:
            self.cpp_info.components["gstcoretracers"].libs = ["gstcoretracers"]
            self.cpp_info.components["gstcoretracers"].libdirs = [os.path.join(self.package_folder, "lib", "gstreamer-1.0")]
            self.cpp_info.components["gstcoretracers"].includedirs = [os.path.join(self.package_folder, "include", "gstreamer-1.0")]
            self.cpp_info.components["gstcoretracers"].requires = gst_dep
            self.cpp_info.components["gstcoretracers"].system_libs = thread_dep
            self.libraries.append("gstcoretracers")

        if not self.options.shared:
            self.cpp_info.components["gstreamer-full-1.0"].libs = ["gstreamer-full-1.0"]
            self.cpp_info.components["gstreamer-full-1.0"].libdirs = [os.path.join(self.package_folder, "lib")]
            self.cpp_info.components["gstreamer-full-1.0"].includedirs = [os.path.join(self.package_folder, "include", "gstreamer-1.0")]
            self.cpp_info.components["gstreamer-full-1.0"].requires = ["glib::glib-2.0", "glib::gobject-2.0", "glib::gmodule-2.0"]
            self.cpp_info.components["gstreamer-full-1.0"].defines = ["GST_STATIC_COMPILATION"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["gstreamer-full-1.0"].system_libs.append("m")
                self.cpp_info.components["gstreamer-full-1.0"].system_libs.append("pthread")

            self.cpp_info.components["gstreamer-full-1.0"].requires.extend(self.libraries)

        if self.options.shared:
            self.runenv_info.define_path("GST_PLUGIN_PATH", os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
