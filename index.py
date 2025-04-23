import os
from typing import Self
# from rich import print

# Parsing librairies
from zipfile import ZipFile
import xml.etree.ElementTree as ET

class DataSet:
    """Represents a single data set within a PASCO Capstone file."""

    def __init__(self, name: str, x_values: str | int, y_values: str, data_size: int, channel_id_name: str | None = None):
        """
        Initialize a DataSet object.

        :param name: The name of the data set (e.g., MeasurementName-ChannelIDName).
        :type name: str
        :param x_values: The path to the independent data file or the time step (if constant).
        :type x_values: str | int
        :param y_values: The path to the dependent data file.
        :type y_values: str
        :param data_size: The size of the data in the dependent file.
        :type data_size: int
        """
        self.name = name
        self.x_values = x_values
        self.y_values = y_values
        self.data_size = data_size
        self.channel_id_name = channel_id_name

    def __repr__(self) -> str:
        """
        Return a string representation of the DataSet object.

        :return: A string describing the DataSet.
        :rtype: str
        """
        if type(self.x_values) == float:
            return f"DataSet(name=\"{self.name}\", x_values={self.x_values}, y_values=\"{self.y_values}\", data_size={self.data_size})"
        else:
            return f"DataSet(name=\"{self.name}\", x_values=\"{self.x_values}\", y_values=\"{self.y_values}\", data_size={self.data_size})"
    def __str__(self) -> str:
        return self.__repr__()

class CapstoneFile:
    """Represents a PASCO Capstone file and its data."""

    def __init__(self, file_path: str):
        """Load a PASCO Capstone file and initialize the object.
        
        :param file_path: The path to the PASCO Capstone file (.cap)
        :type file_path: str
        
        :raises FileNotFoundError: Try double-checking the given file path."""
        if not os.path.isfile(file_path) or os.path.splitext(file_path)[1].lower() != ".cap":
            raise FileNotFoundError(f"Unable to find the PASCO Capstone (.cap) file at {file_path}. Verify the existance and the extension of your file.")
        self.archive_path = file_path
        self.archive = ZipFile(file_path, "r")
        self.data_sets = self.process_archive()

    def process_archive(capstone_file: ZipFile|Self) -> dict[int, list[DataSet]]:
        """Load the data from the PASCO Capstone archive.
        
        :param capstone_file: This parameters appears only if you use the method from the class and not from an object.
        :type capstone_file: ZipFile|CapstoneFile
        
        :returns: A dictionnary with a list of data sets asociated with their group number.
        :rtype: dict[int, list[DataSet]]"""
        if type(capstone_file) == ZipFile:
            archive = capstone_file
        else:
            archive = capstone_file.archive
        main_xml_content = ET.fromstring(archive.read("main.xml"))
        
        # -------------------------------------------------------------------------------------------------------
        # Get the DataSet elements
        # -------------------------------------------------------------------------------------------------------
        # data_sets:
        #     DataSource/DataSet[DataGroupNumber]:
        #         DataSource[MeasurmentName]-DataSource[ChannelIDName]:
        #             DataSource/DataSet/DataSegmentElement/DependentStorageElement[FileName]
        #             DataSource/DataSet/DataSegmentElement/IndependentStorageElement[IntervalCacheInterval|FileName]
        # -------------------------------------------------------------------------------------------------------
        data_sets: dict[int, list[DataSet]] = {}
        data_repository = main_xml_content.find("DataRepository")
        data_source_elements = data_repository.findall("DataSource")

        for data_source_element in data_source_elements:
            data_set_elements = data_source_element.findall("DataSet")
            if not data_set_elements:
                continue
            else:
                # -----------------------------------------------------------------------------------------------
                # Retrieve all the informations about a DataSource
                # -----------------------------------------------------------------------------------------------
                measurment_name = data_source_element.get("MeasurementName")
                channel_id_name = data_source_element.get("ChannelIDName")
                for data_set_element in data_set_elements:
                    data_segment_element  = data_set_element.find("DataSegmentElement")
                    dependent_file        = data_segment_element.find("DependentStorageElement")
                    independent_file      = data_segment_element.find("IndependentStorageElement")
                    group_number          = int(data_set_element.get("DataGroupNumber"))
                    data_size             = int(dependent_file.get("DataCacheDataSize"))
                    dependent_file_name   = dependent_file.get("FileName")
                    independent_file_name = independent_file.get("FileName")
                    if not independent_file_name:
                        independent_file_name = float(independent_file.get("IntervalCacheInterval"))
                    # Safety, to later remove the strange defaultdict(dict)
                    if not group_number in data_sets:
                        data_sets[group_number] = []
                    # Add the set to data_sets
                    data_sets[group_number].append(DataSet(measurment_name, independent_file_name, dependent_file_name, data_size, channel_id_name if channel_id_name else None))
        return data_sets
    
    def __repr__(self):
        representation = f"{os.path.basename(self.archive_path)} at {os.path.realpath(self.archive_path)}:"
        for group_number, data_sets in self.data_sets.items():
            representation += f"\nGroup {group_number}:"
            for data_set in data_sets:
                representation += f"\n{data_set}"
        return representation
    def __str__(self):
        return self.__repr__()

capstone_file = CapstoneFile("tests/test_file.cap")
print(capstone_file)