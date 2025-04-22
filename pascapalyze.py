import sys
import os
import re
from struct import unpack
from collections import defaultdict
from zipfile import ZipFile

# Function to read and extract binary data from a file in an archive
def grok(file_name, data_size, archive: ZipFile):
    if data_size == 0:
        return []
    # Normalize file paths
    file_name = file_name.replace("\\", "/").replace("//", "/")
    try:
        with archive.open(file_name, 'r') as source:
            binary_data = source.read(12 * data_size)
            if not binary_data or len(binary_data) != 12 * data_size:
                print("Data set did not contain advertised number of elements:", binary_data is None, len(binary_data), 12 * data_size)
                return []
            # Extract numbers from binary data
            numbers = [unpack("d", binary_data[offset:offset + 8])[0] for offset in range(4, 12 * data_size, 12)]
            return [numbers]
    except KeyError:
        print("Subfile", file_name, "not available in archive")
        return []

# Function to transpose a list of lists
def transpose(array):
    if not array:
        return []
    max_length = max(len(sublist) for sublist in array)
    extended_array = [list(sublist) + [0] * (max_length - len(sublist)) for sublist in array]
    return list(zip(*extended_array))

# Function to format transposed data into tabulated text
def format_tabulated_data(data):
    transposed_data = transpose(data)
    return "".join(f"{line[0]}\t{line[1]}\n" for line in transposed_data)

# Function to split a text into subsections based on a given string
def segment(text: str, delimiter: str) -> list[str]:
    """Splits the given text with the given delimiter, and keep the delimiter within the splited text.
    
    :param text: The text to split
    :type text: str
    :param delimiter: The delimiter of the substrings created
    :type delimiter: str
    
    :return: The splited text
    :rtype: list[str]"""
    # Use regular expressions to find all occurrences of the delimiter
    matches = [match.start() for match in re.finditer(re.escape(delimiter), text)]
    matches.append(len(text))  # Add the end of the text as the last index
    return [text[start:end] for start, end in zip(matches, matches[1:])]

# Regular expressions to extract specific information
dependent_file_pattern = re.compile(r"<DependentStorageElement [^>]*FileName=\"([^\"]+)\"")
independent_file_pattern = re.compile(r"<IndependentStorageElement [^>]*FileName=\"([^\"]+)\"")
time_step_pattern = re.compile(r"<IndependentStorageElement [^>]*IntervalCacheInterval=\"([^\"]+)\"")
data_group_number_pattern = re.compile(r"DataGroupNumber=\"([^\"]+)\"")
data_size_pattern = re.compile(r"DataCacheDataSize=\"([^\"]+)\"")

# Function to extract data sets from an XML segment
def extract_data_sets(xml_segment):
    dependent_files = list(re.findall(dependent_file_pattern, xml_segment))
    independent_files = list(re.findall(independent_file_pattern, xml_segment))
    group_numbers = list(re.findall(data_group_number_pattern, xml_segment))
    time_steps = list(re.findall(time_step_pattern, xml_segment))
    data_sizes = list(re.findall(data_size_pattern, xml_segment))
    
    if len(data_sizes) > 1 and data_sizes[0] != data_sizes[1]:
        print("Warning: size mismatch")
    
    if dependent_files and independent_files and group_numbers and data_sizes:
        return int(group_numbers[0]), independent_files[0], dependent_files[0], int(data_sizes[0])
    if dependent_files and time_steps and group_numbers and data_sizes:
        return int(group_numbers[0]), float(time_steps[0]), dependent_files[0], int(data_sizes[0])
    
    print("Could not parse: dependent_files, independent_files, time_steps, group_numbers, data_sizes =", dependent_files, independent_files, time_steps, group_numbers, data_sizes)
    return None, None, None, None

# Function to calculate differences between consecutive elements in a list
def calculate_differences(values):
    return map(lambda pair: pair[1] - pair[0], zip(values, values[1:]))

# Regular expressions to extract additional information
data_type_pattern = re.compile(r"MeasurementName=\"([^\"]+)\"")
data_channel_pattern = re.compile(r" ChannelIDName=\"([^\"]+)\"")
set_number_pattern = re.compile(r"ZTDDRBPUsageName=\"[^\"#]*#([0-9]*)[^\"]*\"")
curve_fit_result_pattern = re.compile(r"ZCFDICurveFitParameterResultValue=\"([^\"]+)\"")

# Main function to process data in an archive
def process_archive(archive: ZipFile, output_directory):

    main_xml_content = str(archive.read("main.xml"))
    data_sets = defaultdict(dict) # Creates a dictionary in which accessing missing keys gives an empty dict
    
    # Extract data sets
    for data_source_segment in segment(main_xml_content, "<DataSource "):
        labels = list(re.findall(data_type_pattern, data_source_segment))
        if not labels:
            continue
        label_string = labels[0]
        channels = list(re.findall(data_channel_pattern, data_source_segment))
        if channels:
            label_string += "-" + channels[0]
        
        for data_set_segment in segment(data_source_segment, "<DataSet"):
            group_number, x_data, y_data, data_size = extract_data_sets(data_set_segment)
            print(group_number, x_data, y_data, data_size, labels)
            if group_number is None:
                continue
            data_sets[group_number][label_string] = (x_data, y_data, data_size)
    
    # Extract curve parameters
    curve_fit_parameters = {}
    for renderer_segment in segment(main_xml_content, "<ZRSIndividualRenederer"):
        set_numbers = list(re.findall(set_number_pattern, renderer_segment))
        parameter_segments = segment(renderer_segment, "<ZCFDICurveFitParameterDefinition")
        if len(parameter_segments) != 2:
            continue
        intercept_segment, slope_segment = parameter_segments
        slopes = list(re.findall(curve_fit_result_pattern, slope_segment))
        intercepts = list(re.findall(curve_fit_result_pattern, intercept_segment))
        if set_numbers and slopes and intercepts:
            curve_fit_parameters[int(set_numbers[0])] = (float(intercepts[0]), float(slopes[0]))
    
    # Create output directory
    if not os.path.exists(output_directory + "/"):
        os.mkdir(output_directory + "/")
    
    # Generate output files
    for group_number, group_data in sorted(data_sets.items(), key=lambda item: item[0]):
        output_text = "# dump from cap file\n@WITH G0\n@G0 ON\n"
        legend_index = 0
        for label, (x_data, y_data, data_size) in sorted(group_data.items(), key=lambda item: item[0]):
            if data_size == 0:  # No data for this set
                continue
            print("Processing:", group_number, legend_index, label)
            prefix = f"# {group_number}, field \"{label}\", from {x_data} and {y_data}.\n@TYPE xy\n@    legend string {legend_index} \"{label}\"\n"
            legend_index += 1
            if isinstance(x_data, float):
                dependent_data = grok(y_data, data_size, archive)
                if not dependent_data:
                    continue
                independent_data = [[x_data * i for i in range(len(dependent_data[0]))]]
                combined_data = independent_data + dependent_data
            else:
                combined_data = grok(x_data, data_size, archive) + grok(y_data, data_size, archive)
            if not combined_data:
                print("Failed to read:", legend_index, x_data, y_data, data_size, group_number)
                continue
            body = format_tabulated_data(combined_data)
            output_text += (prefix + body + "&\n")
        open(f"{output_directory}/set{group_number}.txt", "w").write(output_text)

# Main entry point
if __name__ == "__main__":
    input_file = "tests/test_file.cap"
    archive = ZipFile(input_file, 'r')
    output_directory = ".".join(input_file.split(".")[:-1])
    process_archive(archive, output_directory)
