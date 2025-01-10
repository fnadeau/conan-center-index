#include <gst/gst.h>
#include <gst/gstplugin.h>
#include <gst/rtsp-server/rtsp-server.h>

#ifdef GST_RTSP_CLIENT_SINK_STATIC

extern "C"
{
    GST_PLUGIN_STATIC_DECLARE(rtspclientsink);
}

#endif

int main (int argc, char *argv[])
{
    GstRTSPServer *server;
    GMainLoop *loop;

    gst_init(&argc, &argv);

    server = gst_rtsp_server_new();

    loop = g_main_loop_new(NULL, FALSE);

    gst_rtsp_server_attach(server, NULL);

    /* Don't run loop in test */
    //g_main_loop_run(loop);
}
