from django.contrib.admin.apps import AdminConfig


class CasitaAdminConfig(AdminConfig):
    default_site = "tienda_regalos.admin_site.CasitaAdminSite"
