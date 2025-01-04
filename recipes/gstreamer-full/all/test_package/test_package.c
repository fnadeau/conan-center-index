#include <stdio.h>
#include <gst/gst.h>

int main (int argc, char **argv)
{
    GError* error = NULL;
    if (!gst_init_check(&argc, &argv, &error))
    {
        printf("Failed to initialize GStreamer: %s\n", error->message);
        g_error_free(error);
        return 1;
    }

    printf("GStreamer version: %d.%d\n", GST_VERSION_MAJOR, GST_VERSION_MINOR);

    GstRegistry *registry = gst_registry_get();
    const GList *plugins = gst_registry_get_plugin_list(registry);
    for (const GList *it = plugins; it != NULL; it = it->next)
    {
        GstPlugin *plugin = GST_PLUGIN(it->data);
        const gchar *name = gst_plugin_get_name(plugin);
        printf("Plugin: %s\n", name);
    }

    // create simple pipeline with adder
    GstElement *pipeline = gst_pipeline_new("test-pipeline");
    if (!pipeline) {
        printf("Failed to create pipeline\n");
        return 1;
    }

    // cleanup
    gst_object_unref(pipeline);

    gst_deinit();

    return 0;
}