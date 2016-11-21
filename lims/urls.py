from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from rest_framework import routers

from lims.users.views import ObtainAuthToken, UserViewSet, GroupViewSet
from lims.permissions.views import PermissionViewSet

from lims.shared.views import OrganismViewSet, TriggerAlertStatusViewSet, TriggerSetViewSet, \
    TriggerViewSet, TriggerSubscriptionViewSet

from lims.orders.views import OrderViewSet
from lims.addressbook.views import AddressViewSet
from lims.pricebook.views import PriceBookViewSet

from lims.inventory.views import (InventoryViewSet,
                                  SetViewSet, MeasureViewSet, ItemTypeViewSet, LocationViewSet)
from lims.codonusage.views import CodonUsageTableViewSet
from lims.projects.views import (ProjectViewSet, ProductViewSet, ProductStatusViewSet)
from lims.workflows.views import (WorkflowViewSet, RunViewSet,
                                  TaskViewSet, TaskFieldViewSet)

from lims.filetemplate.views import FileTemplateViewSet

from lims.equipment.views import EquipmentViewSet, EquipmentReservationViewSet
from lims.drivers.views import CopyFileDriverViewSet

from lims.crm.views import (CRMUserView, CRMProjectView, CRMUpdateProjectView, CRMLinkView,
                            CRMUpdateAccountView)

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet, base_name='orders')
router.register(r'addresses', AddressViewSet, base_name='addresses')
router.register(r'pricebooks', PriceBookViewSet, base_name='pricebooks')
router.register(r'codonusage', CodonUsageTableViewSet, base_name='codonusage')

router.register(r'users', UserViewSet, base_name='users')
router.register(r'groups', GroupViewSet, base_name='groups')
router.register(r'permissions', PermissionViewSet, base_name='permissions')

router.register(r'inventory', InventoryViewSet, base_name='inventory')
router.register(r'inventorysets', SetViewSet, base_name='inventorysets')
router.register(r'organisms', OrganismViewSet, base_name='organisms')
router.register(r'measures', MeasureViewSet, base_name='measures')
router.register(r'itemtypes', ItemTypeViewSet, base_name='itemtypes')
router.register(r'locations', LocationViewSet, base_name='locations')

router.register(r'equipment', EquipmentViewSet, base_name='equipment')
router.register(r'equipmentreservation', EquipmentReservationViewSet,
                base_name='equipmentreservation')

router.register(r'projects', ProjectViewSet, base_name='projects')
router.register(r'products', ProductViewSet, base_name='products')
router.register(r'productstatuses', ProductStatusViewSet, base_name='productstatuses')
router.register(r'workflows', WorkflowViewSet, base_name='workflows')
router.register(r'runs', RunViewSet, base_name='runs')
router.register(r'tasks', TaskViewSet, base_name='tasks')
router.register(r'taskfields', TaskFieldViewSet, base_name='taskfields')
router.register(r'filetemplates', FileTemplateViewSet, base_name='filetemplates')
router.register(r'copyfiles', CopyFileDriverViewSet, base_name='copyfiles')

router.register(r'triggers', TriggerViewSet, base_name='triggers')
router.register(r'triggersets', TriggerSetViewSet, base_name='triggersets')
router.register(r'subscriptions', TriggerSubscriptionViewSet, base_name='subscriptions')
router.register(r'alerts', TriggerAlertStatusViewSet, base_name='alerts')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/token/', ObtainAuthToken.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^crm/user/', CRMUserView.as_view()),
    url(r'^crm/project/update/', CRMUpdateProjectView.as_view()),
    url(r'^crm/account/update/', CRMUpdateAccountView.as_view()),
    url(r'^crm/project/', CRMProjectView.as_view()),
    url(r'^crm/link/', CRMLinkView.as_view()),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
