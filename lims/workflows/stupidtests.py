from lims.workflows.models import TestTask
from lims.workflows.actions import Input, Output, Variable, Calculation
i1 = Input(measure='ul', inventory_item_type='Consumable', amount=10)
i2 = Input(measure='ul', inventory_item_type='Consumable', amount=30)
o = Output(measure='ul', inventory_object_type='Plasmid', amount=0)
v = Variable(measure='ul', value=0)
c = Calculation(calculation='{test_input} + {test_input2}')
tt = TestTask(name='test task', test_input=i1, test_input2=i2, test_output=o, test_variable=v, test_calculation=c)
tt.save()
cc = tt.test_calculation
cc.perform_calculation(tt)


from lims.workflows.models import TestTask
tt = TestTask.objects.get(name='test task')
cc = tt.test_calculation
cc.perform_calculation(tt)
cc.instance_to_dict(tt)


from lims.workflows.models import TestTask                                                                        
from lims.workflows.actions import Calculation
tt = TestTask.objects.get(name='test task')
cn = Calculation('{test_input} + {nonexistant_input}')
cn.perform_calculation(tt)
