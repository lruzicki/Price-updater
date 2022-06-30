from functions import *

object_scheduler = SchedulerSetUp()

while True:
    try:
        option = int(input('''Input number to select option: \n
        1. Run scheduler to update prices everyday\n
        2. Update changes once\n
        3. Generate excel file with products\n
        your option: '''))
    except:
        print("\nInput only 1, 2 or 3!")
    else:
        if option == 1:
            schedule.every(1).days.do(object_scheduler.startScheduler())
        elif option == 2:
            object_scheduler.startScheduler()
        elif option == 3:
            object_scheduler.importToExcel()
        break




