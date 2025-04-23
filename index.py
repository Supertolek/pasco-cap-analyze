import os
from typing import Self

from struct import unpack

import numpy as np
import matplotlib.pyplot as plt

# Parsing librairies
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def grok(file_name: str, data_size: int, archive: ZipFile):
    if data_size == 0:
        return []
    try:
        with archive.open(
            os.path.normpath(file_name).replace("\\", "/"), "r"
        ) as source:
            binary_data = source.read(12 * data_size)
            if not binary_data or len(binary_data) != 12 * data_size:
                print(
                    "Data set did not contain advertised number of elements:",
                    binary_data is None,
                    len(binary_data),
                    12 * data_size,
                )
                return []
            # Extract numbers from binary data
            numbers = [
                unpack("d", binary_data[offset : offset + 8])[0]
                for offset in range(4, 12 * data_size, 12)
            ]
            return numbers
    except KeyError:
        print("Subfile", file_name, "not available in archive")
        return []


def frange(start: int | float, stop: int | float, step: int | float) -> list:
    """Range, but for floats"""
    list_of_items = []
    for index in range(int((stop - start) / step)):
        list_of_items.append(round(start + step * index, 12))
    return list_of_items


class DataSet:
    """Represents a single data set within a PASCO Capstone file."""

    def __init__(
        self,
        name: str,
        x_values: str | int,
        y_values: str,
        data_size: int,
        channel_id_name: str | None = None,
        archive: ZipFile | None = None,
    ):
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
        if archive:
            if type(x_values) == str:
                self.x_values = grok(x_values, data_size, archive)
            elif type(x_values) == float:
                self.x_values = list(frange(0, x_values * data_size, (x_values)))
            else:
                self.x_values = x_values
            self.y_values = grok(y_values, data_size, archive)
        else:
            self.x_values = x_values
            self.y_values = y_values
        self.data_size = data_size
        self.channel_id_name = channel_id_name

    def plot(self, show: bool = True):
        """
        Uses MatPlotLib to plot the data on a graph.
        """
        if not (type(self.x_values) == list and type(self.y_values) == list):
            raise TypeError(
                f"The given data is in the wrong format. Expected list (or Array like), got {type(self.x_values)} and  {type(self.y_values)}."
            )
        print(len(self.x_values), len(self.y_values))
        print(self.x_values, self.y_values)
        plt.plot(self.x_values, self.y_values)
        if show:
            plt.show()

    def __repr__(self) -> str:
        """
        Return a string representation of the DataSet object.

        :return: A string describing the DataSet.
        :rtype: str
        """
        representation = f'DataSet(name="{self.name}", '

        if type(self.x_values) == float:
            representation += f"x_values={self.x_values}, "
        elif type(self.x_values) == list:
            representation += f"x_values={self.x_values if len(self.x_values) <= 2 else f"[{self.x_values[0]},...,{self.x_values[-1]}]"}, "
        else:
            representation += f'x_values="{self.x_values}", '

        if type(self.y_values) == float:
            representation += f"y_values={self.y_values}, "
        elif type(self.y_values) == list:
            representation += f"y_values={self.y_values if len(self.y_values) <= 2 else f"[{self.y_values[0]}, ..., {self.y_values[-1]}]"}, "
        else:
            representation += f'y_values="{self.y_values}", '

        representation += f"data_size={self.data_size})"
        return representation

    def __str__(self) -> str:
        return self.__repr__()


class CapstoneFile:
    """Represents a PASCO Capstone file and its data."""

    def __init__(self, file_path: str):
        """Load a PASCO Capstone file and initialize the object.

        :param file_path: The path to the PASCO Capstone file (.cap)
        :type file_path: str

        :raises FileNotFoundError: Try double-checking the given file path."""
        if (
            not os.path.isfile(file_path)
            or os.path.splitext(file_path)[1].lower() != ".cap"
        ):
            raise FileNotFoundError(
                f"Unable to find the PASCO Capstone (.cap) file at {file_path}. Verify the existance and the extension of your file."
            )
        self.archive_path = file_path
        self.archive = ZipFile(file_path, "r")
        self.data_sets: dict[int, list[DataSet]] = self.process_archive()

    def process_archive(capstone_file: ZipFile | Self) -> dict[int, list[DataSet]]:
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
                    data_segment_element = data_set_element.find("DataSegmentElement")
                    dependent_file = data_segment_element.find(
                        "DependentStorageElement"
                    )
                    independent_file = data_segment_element.find(
                        "IndependentStorageElement"
                    )
                    group_number = int(data_set_element.get("DataGroupNumber"))
                    data_size = int(dependent_file.get("DataCacheDataSize"))
                    dependent_file_name = dependent_file.get("FileName")
                    independent_file_name = independent_file.get("FileName")
                    if not independent_file_name:
                        independent_file_name = float(
                            independent_file.get("IntervalCacheInterval")
                        )
                    # Safety, to later remove the strange defaultdict(dict)
                    if not group_number in data_sets:
                        data_sets[group_number] = []
                    # Add the set to data_sets
                    data_sets[group_number].append(
                        DataSet(
                            measurment_name,
                            independent_file_name,
                            dependent_file_name,
                            data_size,
                            channel_id_name if channel_id_name else None,
                            capstone_file.archive,
                        )
                    )
        return data_sets

    def plot(self):
        for group_id, group in self.data_sets.items():
            for data_set in group:
                data_set.plot(False)
        plt.show()

    def to_csv(self, decimal_separator: str = ".", cell_separator: str = ";"):
        original_table: list[list[int | str]] = []
        max_column_length = 1
        for group_id, group in self.data_sets.items():
            columns = []
            for data_set in group:
                column_x = ["", data_set.name]
                column_y = ["", ""]
                if type(data_set.x_values) == list and type(data_set.y_values) == list:
                    column_x.extend(data_set.x_values)
                    column_y.extend(data_set.y_values)
                columns.append(column_x)
                columns.append(column_y)
                max_column_length = max(max_column_length, len(column_x), len(column_y))
            if columns and columns[0]:
                columns[0][0] = f"Group {group_id}"
            else:
                columns.append([f"Group {group_id} (empty)"])
            original_table.extend(columns)

        for column_index, column in enumerate(original_table):
            if len(column) < max_column_length:
                original_table[column_index].extend(
                    [""] * (max_column_length - len(column))
                )

        output = "\n".join(
            [
                cell_separator.join(
                    [
                        (
                            str(column[row_index])
                            if type(column[row_index]) != float
                            else str(column[row_index]).replace(".", decimal_separator)
                        )
                        for column in original_table
                    ]
                )
                + cell_separator
                for row_index in range(max_column_length)
            ]
        )
        return output

    def __repr__(self):
        representation = f"{os.path.basename(self.archive_path)} at {os.path.realpath(self.archive_path)}:"
        for group_number, data_sets in self.data_sets.items():
            representation += f"\nGroup {group_number}:"
            for data_set in data_sets:
                representation += f"\n{data_set}"
        return representation

    def __str__(self):
        return self.__repr__()
