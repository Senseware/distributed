from django.contrib import admin


from distributed.models import DistributedSource, DistributedSourceModel


class DistributedSourceModelInline(admin.TabularInline):
    model = DistributedSourceModel
    fields = ('model_class', 'api_url', 'active', 'last_sync', 'last_sync_message')
    readonly_fields = ('last_sync','last_sync_message',)
    extra = 0



class DistributedSourceAdmin(admin.ModelAdmin):
    fields = ('name','active', 'api_url','last_sync', 'api_username','api_password', 'notes','last_sync_message')
    readonly_fields = ('last_sync','last_sync_message',)
    inlines = [DistributedSourceModelInline,]
admin.site.register(DistributedSource, DistributedSourceAdmin)
