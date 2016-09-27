""" This module implements basic abstractions for MAC configuration and control on sensor nodes.
"""
import abc
import logging


class MACManager(object):
    """Abstract MAC manager class listing all the mandatory MACManager functions.
    These functions must be implemented by the subclassess.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def update_macconfiguration(self, param_key_values_dict):
        """Update the current MAC configuration.
        This function takes a dictionary argument containing parameter key-value pairs.
        This function returs a dictionary containing parameter key-error_code pairs.
        Args:
            parameter_key_values (Dict[str,Any]): a dictionary argument containing parameter key-value pairs.
        Returns:
            Dict[str, int]: This function returs a dictionary containing parameter key-error_codes pairs.
        """
        return -1

    @abc.abstractmethod
    def read_macconfiguration(self, param_key_list):
        """Reads the current MAC configuration.
        This function takes a list of parameter keys as arguments.
        This function returns a dictionary containing parameter key-value pairs.
        Args:
            parameter_keys (List[str]): a list of parameter keys as arguments.
        Returns:
            Dict[str,Any]: a dictionary containing parameter key-value pairs.
        """
        return -1

    @abc.abstractmethod
    def get_measurements(self, measurement_key_list):
        """Monitor the current MAC behaviour in a pull based manner.
        This function takes a list of measurement keys as arguments.
        This function returns a dictionary containing measurement key-value pairs.
        Args:
            measurement_keys (List[str]): a list of measurement keys as arguments.
        Returns:
            Dict[str,Any]: a dictionary containing measurement key-value pairs.
        """
        return -1

    @abc.abstractmethod
    def get_measurements_periodic(self, measurement_key_list, collect_period, report_period, num_iterations, report_callback):
        """Monitor the current MAC behaviour periodically in a pull based manner.
        This function takes a list of measurement keys and configuration alues for the periodic collection as arguments.
        This function returns an error code.
        Args:
            measurement_keys (List[str]): a list of measurement keys as arguments
            collect_period (int): Period between measurements.
            collect_iterations (int): Number of collect periods.
            report_period (int): Period between reports (report_period<=collect_period*collect_iterations)
            report_callback (Callable[[str,Dict[str,List[Any]]], None]): Callback with arguments radio_platform and measurement report.
        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        return -1

    @abc.abstractmethod
    def subscribe_events(self, event_key_list, event_callback, event_duration):
        """Monitor the MAC behaviour asynchroniously in a push based manner by registering for events.
        This function takes a list of event keys and an event callback as arguements.
        This function returns an error code.
        Args:
            event_keys (List[str]): a list of event keys
            event_callback (Callable[[str,str,Any],None]): Callback with arguments radio_platform, event name and event value.
        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        return -1

    @abc.abstractmethod
    def activate_radio_program(self, name):
        """Activate a MAC radio program.
        Args:
            name (str): Name of the MAC radioprogram (CSMA, TDMA, TSCH).
        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        return -1

    @abc.abstractmethod
    def get_radio_info(self):
        """Returns a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.
        Returns:
            UPI_R.radio_info_t: a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.
        """
        return -1

    @abc.abstractmethod
    def get_radio_platforms(self):
        """Returns a list of radio_platform_t objects containing interface name and platform name.
        Returns:
            List[UPI_R.radio_platform_t]: a list of radio_platform_t objects containing interface name and platform name.
        """
        return -1

    @abc.abstractmethod
    def get_hwaddr_list(self):
        """Returns the macaddress of the interface.
        Returns:
            int: the macaddress
        """
        return -1


class LocalMACManager(MACManager):
    """Local MAC manager class implementing all the mandatory MACManager functions.
    This class can be extended to support extra functions, specific to a MAC protocol (CSMA,TDMA,TSCH)
    """

    def __init__(self, control_engine):
        """Creates a Local MAC Manager object.

        Args:
            local_engine (LocalManager): a reference to the local WiSHFUL engine.
        """
        self.control_engine = control_engine
        self.log = logging.getLogger("local_mac_manager")
        self.radio_platforms = control_engine.radio.blocking(True).iface("lowpan0").get_radio_platforms()
        self.mac_address_radio_platform_dict = {}
        self.radio_platform_mac_address_dict = {}
        for radio_platform in self.radio_platforms:
            mac_address = control_engine.radio.blocking(True).iface(radio_platform).get_hwaddr()
            self.mac_address_radio_platform_dict[mac_address] = radio_platform
            self.radio_platform_mac_address_dict[radio_platform] = mac_address
        pass

    def __execute_local_upi_func(self, UPIfunc, UPIargs, UPIkwargs, mac_address_list):
        # first get the radio platforms on which the UPI call needs to be executed
        radio_platforms = []
        for mac_address in mac_address_list:
            radio_platforms.append(self.mac_address_radio_platform_dict[mac_address])
        # now execute the UPI call
        ret = {}
        for radio_platform in radio_platforms:
            ret[self.radio_platform_mac_address_dict[radio_platform]] = self.control_engine.blocking(
                True).iface(radio_platform).exec_cmd("radio", UPIfunc, UPIargs, UPIargs)
        return ret

    def update_macconfiguration(self, param_key_values_dict, mac_address_list=None):
        """Update the current MAC configuration.
        This function takes a dictionary argument containing parameter key-value pairs.
        This function returs a dictionary containing parameter key-error_code pairs.

        Args:
            parameter_key_values (Dict[str,Any]): a dictionary containing parameter key-value pairs.
             radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str, int]: This function returs a dictionary containing parameter key-error_codes pairs.
        """
        UPIfunc = "set_parameters"
        UPIargs = (param_key_values_dict)
        UPIkwargs = {"param_key_values_dict": param_key_values_dict}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def read_macconfiguration(self, param_key_list, mac_address_list=None):
        """Update the current MAC configuration.
        This function takes a list of parameter keys as arguments.
        This function returns a dictionary containing parameter key-value pairs.

        Args:
            parameter_keys (List[str]): a list of parameter keys
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str,Any]: a dictionary containing parameter key-value pairs.
        """
        UPIfunc = "get_parameters"
        UPIargs = (param_key_list)
        UPIkwargs = {'param_key_list': param_key_list}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_measurements(self, measurement_key_list, mac_address_list=None):
        """Monitor the current MAC behaviour in a pull based manner.
        This function takes a list of measurement keys as arguments.
        This function returns a dictionary containing measurement key-value pairs.

        Args:
            measurement_keys (List[str]): a list of measurement keys
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str,Any]: a dictionary containing measurement key-value pairs.
        """
        UPIfunc = "get_measurements"
        UPIargs = (measurement_key_list)
        UPIkwargs = {'measurement_key_list': measurement_key_list}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_measurements_periodic(self, measurement_key_list, collect_period, report_period, num_iterations, report_callback, mac_address_list=None):
        """Monitor the current MAC behaviour periodically in a pull based manner.
        This function takes a list of measurement keys and configuration alues for the periodic collection as arguments.
        This function returns an error code.

        Args:
            measurement_keys (List[str]): a list of measurement keys
            collect_period (int): Period between measurements.
            collect_iterations (int): Number of collect periods.
            report_period (int): Period between reports (report_period<=collect_period*collect_iterations)
            report_callback (Callable[[str,Dict[str,List[Any]]], None]): Callback with arguments radio_platform and measurement report.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "get_measurements_periodic"
        UPIargs = (measurement_key_list, collect_period, report_period, num_iterations, report_callback)
        UPIkwargs = {'measurement_key_list': measurement_key_list, 'collect_period': collect_period,
                     'report_period': report_period, 'num_iterations': num_iterations,
                     'report_callback': report_callback}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def subscribe_events(self, event_key_list, event_callback, event_duration, mac_address_list=None):
        """Monitor the MAC behaviour asynchroniously in a push based manner by registering for events.
        This function takes a list of event keys and an event callback as arguements.
        This function returns an error code.

        Args:
            event_keys (List[str]): a list of event keys
            event_callback (Callable[[str,str,Any],None]): Callback with arguments radio_platform, event name and event value.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "subscribe_events"
        UPIargs = (event_key_list, event_callback, event_duration)
        UPIkwargs = {'event_key_list': event_key_list,
                     'event_callback': event_callback, 'event_duration': event_duration}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def activate_radio_program(self, name, mac_address_list=None):
        """Activate a MAC radio program.

        Args:
            name (str): Name of the MAC radioprogram (CSMA, TDMA, TSCH).
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "activate_radio_program"
        UPIargs = (name)
        UPIkwargs = {'name': name}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_radio_info(self, mac_address_list=None):
        """Returns a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.

        Args:
            radio_platforms (List[str], optional): list of radio platforms
        Returns:
            UPI_R.radio_info_t: a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.
        """
        UPIfunc = "get_radio_info"
        UPIargs = ()
        UPIkwargs = {}
        return self.__execute_local_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_hwaddr_list(self):
        """Returns the macaddress of the interface.

        Args:
            radio_platforms (List[str], optional): list of radio platforms
        Returns:
            int: the macaddress
        """
        return self.mac_address_radio_platform_dict.keys()


class GlobalMACManager(MACManager):
    """ Class doc """

    def __init__(self, control_engine):
        """ Class initialiser """
        self.control_engine = control_engine
        self.log = logging.getLogger("global_mac_manager")
        self.nodes = []
        self.nodes_radio_platform_dict = {}
        self.mac_address_node_radioplatform_dict = {}
        pass

    def add_node(self, node):
        self.nodes.append(node)
        radio_platforms = self.control_engine.node(node).blocking(True).iface("lowpan0").radio.get_radio_platforms()
        self.nodes_radio_platform_dict[node] = radio_platforms
        for radio_platform in radio_platforms:
            mac_addr = self.control_engine.node(node).blocking(True).iface(radio_platform).radio.get_hwaddr()
            self.mac_address_node_radioplatform_dict[mac_addr] = [node, radio_platform]

    def remove_node(self, node):
        self.nodes.remove(node)
        del self.nodes_radio_platform_dict[node]
        for mac_addr in self.mac_address_node_radioplatform_dict.keys():
            if self.mac_address_node_radioplatform_dict[mac_addr][0] == node:
                del self.mac_address_node_radioplatform_dict[mac_addr]
                break

    def __execute_global_upi_func(self, UPIfunc, UPIargs, UPIkwargs, mac_address_list=None):
        if mac_address_list is None:
            mac_address_list = self.mac_address_node_radioplatform_dict.keys()
        ret = {}
        for mac_addr in mac_address_list:
            node = self.mac_address_node_radioplatform_dict[mac_addr][0]
            radio_platform = self.mac_address_node_radioplatform_dict[mac_addr][1]
            ret[mac_addr] = self.control_engine.blocking(True).node(node).iface(
                radio_platform).exec_cmd("radio", UPIfunc, UPIargs, UPIkwargs)
        return ret

    def update_macconfiguration(self, param_key_values_dict, mac_address_list=None):
        """Update the current MAC configuration.
        This function takes a dictionary argument containing parameter key-value pairs.
        This function returs a dictionary containing parameter key-error_code pairs.

        Args:
            parameter_key_values (Dict[str,Any]): a dictionary argument containing parameter key-value pairs.
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str, int]: This function returs a dictionary containing parameter key-error_codes pairs.
        """
        UPIfunc = "set_parameters"
        UPIargs = (param_key_values_dict)
        UPIkwargs = {'param_key_values_dict': param_key_values_dict}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def read_macconfiguration(self, param_key_list, mac_address_list=None):
        """Update the current MAC configuration.
        This function takes a list of parameter keys as arguments.
        This function returns a dictionary containing parameter key-value pairs.

        Args:
            parameter_keys (List[str]): a list of parameter keys as arguments.
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str,Any]: a dictionary containing parameter key-value pairs.
        """
        UPIfunc = "get_parameters"
        UPIargs = (param_key_list)
        UPIkwargs = {'param_key_list': param_key_list}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_measurements(self, measurement_key_list, mac_address_list=None):
        """Monitor the current MAC behaviour in a pull based manner.
        This function takes a list of measurement keys as arguments.
        This function returns a dictionary containing measurement key-value pairs.

        Args:
            measurement_keys (List[str]): a list of measurement keys
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            Dict[str,Any]: a dictionary containing measurement key-value pairs.
        """
        UPIfunc = "get_measurements"
        UPIargs = (measurement_key_list)
        UPIkwargs = {'measurement_key_list': measurement_key_list}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_measurements_periodic(self, measurement_key_list, collect_period, report_period, num_iterations, report_callback, mac_address_list=None):
        """Monitor the current MAC behaviour periodically in a pull based manner.
        This function takes a list of measurement keys and configuration alues for the periodic collection as arguments.
        This function returns an error code.

        Args:
            measurement_keys (List[str]): a list of measurement keys
            collect_period (int): Period between measurements.
            collect_iterations (int): Number of collect periods.
            report_period (int): Period between reports (report_period<=collect_period*collect_iterations)
            report_callback (Callable[[str,Dict[str,List[Any]]], None]): Callback with arguments radio_platform and measurement report.
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "get_measurements_periodic"
        UPIargs = (measurement_key_list, collect_period, report_period, num_iterations, report_callback)
        UPIkwargs = {'measurement_key_list': measurement_key_list, 'collect_period': collect_period,
                     'report_period': report_period, 'num_iterations': num_iterations, 'report_callback': report_callback}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def subscribe_events(self, event_keys, event_callback, event_duration, mac_address_list=None):
        """Monitor the MAC behaviour asynchroniously in a push based manner by registering for events.
        This function takes a list of event keys and an event callback as arguements.
        This function returns an error code.

        Args:
            event_keys (List[str]): a list of event keys
            event_callback (Callable[[str,str,Any],None]): Callback with arguments radio_platform, event name and event value.
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "subscribe_events"
        UPIargs = (event_keys, event_callback, event_duration)
        UPIkwargs = {'event_keys': event_keys, 'event_callback': event_callback, 'event_duration': event_duration}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_radio_info(self, mac_address_list=None):
        """Returns a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.

        Args:
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms
        Returns:
            UPI_R.radio_info_t: a radio_info_t object containing all parameter, measurement and event keys as well as the available radio programs.
        """
        UPIfunc = "get_radio_info"
        UPIargs = ()
        UPIkwargs = {}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def activate_radio_program(self, name, mac_address_list=None):
        """Activate a MAC radio program.

        Args:
            name (str): Name of the MAC radioprogram (CSMA, TDMA, TSCH).
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms

        Returns:
            int: error code (0 = success, -1 = fail, >=1 errno value)
        """
        UPIfunc = "activate_radio_program"
        UPIargs = (name)
        UPIkwargs = {'name': name}
        return self.__execute_global_upi_func(UPIfunc, UPIargs, UPIkwargs, mac_address_list)

    def get_hwaddr_list(self):
        """Returns the macaddress of the interface.

        Args:
            nodes (List[Node]): a list of wishful nodes to which the function must be delegated.
            radio_platforms (List[str], optional): list of radio platforms
        Returns:
            int: the macaddress
        """
        return self.mac_address_node_radioplatform_dict.keys()