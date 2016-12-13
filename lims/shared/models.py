from django.db import models
import reversion
import six
from django.contrib.auth.models import User
from django.db.models.signals import post_save  # noqa
from channels import Channel


@reversion.register()
class Organism(models.Model):
    """
    Basic information on an Organism
    """
    name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


@reversion.register()
class LimsPermission(models.Model):
    """
    Allow access to the LIMS system
    """

    class Meta:
        permissions = (
            ('lims_access', 'Access LIMS system',),
        )


@reversion.register()
class TriggerSet(models.Model):
    LOW = 'L'
    MEDIUM = 'M'
    HIGH = 'H'
    SEVERITY_CHOICES = (
        (LOW, 'low',),
        (MEDIUM, 'medium',),
        (HIGH, 'high',)
    )
    model = models.CharField(max_length=80, blank=False, null=False, default='Item')
    severity = models.CharField(blank=False, null=False, max_length=1, choices=SEVERITY_CHOICES,
                                default=LOW)
    name = models.TextField(blank=False, null=False, default="My Trigger")
    email_title = models.CharField(max_length=255, blank=False, null=False,
                                   default='Alert from GET LIMS')
    email_template = \
        models.TextField(blank=False, null=False,
                         default='{name}: {model} instance {instance} triggered on {date}.')

    @staticmethod
    def _fire_triggersets(sender, instance=None, created=False, raw=False, **kwargs):
        if raw:
            return  # We do not want to fire on loading raw data
        model = sender.__name__
        for triggerset in TriggerSet.objects.filter(model=model):
            if triggerset.all_triggers_fire(instance, created):
                email_recipients = []
                alert = TriggerAlert.objects.create(triggerset=triggerset, instance_id=instance.id)
                for subscription in triggerset.subscriptions.all():
                    alert.statuses.create(user=subscription.user,
                                          status=TriggerAlertStatus.ACTIVE,
                                          last_updated_by=subscription.user)
                    if subscription.email:
                        email_recipients.append(subscription.user.email)
                alert.save()
                if len(email_recipients) > 0:
                    content = triggerset._complete_email_template(instance, alert.fired)
                    message = {
                        'title': triggerset.email_title,
                        'content': content,
                        'recipients': email_recipients,
                    }
                    Channel('send-email').send(message)

    def all_triggers_fire(self, instance=None, created=False):
        for trigger in self.triggers.all():
            if not trigger.trigger_fires(instance, created):
                return False
        return True

    def _complete_email_template(self, instance, fired):
        content = self.email_template
        replace_fields = {
            "model": self.model,
            "instance": instance.id,
            "name": self.name,
            "date": fired.strftime("%Y-%m-%d %H:%M:%S")
        }
        for field, value in replace_fields.items():
            content = content.replace('{{{}}}'.format(field), repr(value))
        return content


@reversion.register()
class Trigger(models.Model):
    EQ = '=='
    LE = '<='
    GE = '>='
    LT = '<'
    GT = '>'
    NE = '!='
    OPERATOR_CHOICES = (
        (LT, 'less than',),
        (LE, 'less than or equal to',),
        (EQ, 'equal to',),
        (GE, 'greater than or equal to',),
        (GT, 'greater than',),
        (NE, 'not equal to',),
    )
    triggerset = models.ForeignKey(TriggerSet, related_name="triggers")
    field = models.CharField(max_length=80, blank=False, null=False, default='id')
    operator = models.CharField(blank=False, null=False, max_length=2, choices=OPERATOR_CHOICES,
                                default=EQ)
    value = models.CharField(max_length=255, blank=False, null=False, default='1')
    fire_on_create = False

    def trigger_fires(self, instance=None, created=False):
        if not instance:
            return False
        if created and not self.fire_on_create:
            return False
        if not hasattr(instance, self.field):
            return False
        test_value = self.value
        instance_value = getattr(instance, self.field)
        if isinstance(instance_value, object):
            instance_value = str(instance_value)
        if isinstance(instance_value, six.string_types):
            # Wrap only strings in quotes
            instance_value = "r'%s'" % instance_value
        if isinstance(test_value, six.string_types):
            test_value = "r'%s'" % self.value
        expr = '%s %s %s' % (instance_value, self.operator, test_value)
        # TODO: Replace eval with something less worrying
        return eval(expr, {"__builtins__": {}})


@reversion.register()
class TriggerAlert(models.Model):
    triggerset = models.ForeignKey(TriggerSet, related_name="alerts")
    fired = models.DateTimeField(auto_now_add=True)
    instance_id = models.IntegerField()


@reversion.register()
class TriggerAlertStatus(models.Model):
    ACTIVE = 'A'
    SILENCED = 'S'
    DISMISSED = 'D'
    STATUS_CHOICES = (
        (ACTIVE, 'Active',),
        (SILENCED, 'Silenced',),
        (DISMISSED, 'Dismissed',),
    )
    user = models.ForeignKey(User, related_name="alerts")
    status = models.CharField(blank=False, null=False, max_length=1, choices=STATUS_CHOICES,
                              default=ACTIVE)
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name="updatedalerts", blank=True, null=True,
                                        on_delete=models.SET_NULL)
    triggeralert = models.ForeignKey(TriggerAlert, related_name="statuses")


@reversion.register()
class TriggerSubscription(models.Model):
    triggerset = models.ForeignKey(TriggerSet, related_name="subscriptions")
    user = models.ForeignKey(User)
    email = models.BooleanField(default=False, blank=False, null=False)
