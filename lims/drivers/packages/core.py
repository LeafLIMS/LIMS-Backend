class Driver(object):

    def __init__(self, task_data):
        # Use the task data to make files/drive equipment
        self.task_data = task_data

    def drive(self):
        """
        Drive the machine fully

        Sends and listens to commands to directly control
        the relevant equipment.
        """
        pass

    def fetch(self):
        """
        Fetch one of more files from a directory
        """
        pass

    def put(self):
        """
        Put one or more files in a directory
        """
        pass

    def ask(self):
        """
        Find out the current status of the equipment
        """
        pass


class DummyDriver(Driver):
    """
    Does nothing!
    """
