import argparse
import os

from extract_line_from_files.core import scan_dirs, scan_file

data_folder = 'data'


def handle_input(file, query, copyline, outfile, verbose):
    global data_folder
    if outfile:
        dirname = os.path.dirname(__file__)
        root_data_folder = os.path.join(dirname, data_folder)
        if not os.path.exists(root_data_folder):
            os.makedirs(root_data_folder)
        csv_filename = os.path.join(root_data_folder, 'extracted_data.csv')
    else:
        csv_filename = ""
    if args.recursive:
        scan_dirs(file, query, copyline, csv_filename, verbose)
    else:
        scan_file(file, query, copyline, csv_filename, verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scans Java files for a StackOverflow links and returns those in a csv sanitized as much as possible.")
    parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
    parser.add_argument('-r', '--recursive', action='store_true', help="scan a directory recursively.")
    parser.add_argument('-o', '--output-file', action='store_true',
                        help="save output in csv file found in data/extracted_data.csv.")
    parser.add_argument('-c', '--copy-line', action='store_true',
                        help="copy first line of the scanned file(s), removing comment characters like \"//\". This works "
                             "in tandem with dsc_cli.py which writes the link to the raw file in the first line with a "
                             "preceding \"//\".")
    parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

    args = parser.parse_args()
    handle_input(args.file[0], "stackoverflow.com", args.copy_line, args.output_file, args.verbose)
