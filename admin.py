from django.contrib import admin


from distributed.models import DistributedSource, DistributedSourceModel


class DistributedSourceModelInline(admin.TabularInline):
    model = DistributedSourceModel
    fields = ('resource_name', 'api_url', 'order', 'active', 'last_sync', 'last_sync_message')
    readonly_fields = ('last_sync','last_sync_message',)
    extra = 0



class DistributedSourceAdmin(admin.ModelAdmin):
    fields = ('name','active', 'api_url','last_sync', 'api_username','api_password', 'notes','last_sync_message')
    readonly_fields = ('last_sync','last_sync_message',)
    inlines = [DistributedSourceModelInline,]

    def save_related(self, request, form, formsets, change):
        super(DistributedSourceAdmin, self).save_related(request, form, formsets, change)
        form.instance.sync()
admin.site.register(DistributedSource, DistributedSourceAdmin)
