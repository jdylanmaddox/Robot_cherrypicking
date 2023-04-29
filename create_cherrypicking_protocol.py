# import packages
import pandas as pd
import os
import glob
import numpy as np


def cherrypick(base_name='2022_12_04_p1', sample_vol=5.0, plate_type='nest_96_wellplate_100ul_pcr_full_skirt', tip_type='filtered', excel_file='yes', simulate_run='yes'):
    if sample_vol < 1.0:
        print('*** Sample volume (i.e. sample_vol) must be greater than 1.0 µl, but 2.0 µl is the ideal minimum')
        print('*** You used ' + str(sample_vol) + ' µl')
        quit()

    # option to use script simply to export Excel worksheets of a single file into separate csv files
    only_for_csv_conversion = 'no'

    # create well locations for the destination plate
    rows = 'ABCDEFGH'
    cols = range(1, 13)
    wells = [f"{row}{col}" for col in cols for row in rows]
    wells = wells + wells

    # create a list of the destination plate well numbers
    cherry_plate_num = [1] * 96 + [2] * 96

    # convert multiple Excel worksheets to individual csv files
    if excel_file == 'yes':

        # check for files in source_CSVs directory
        # ask to delete files if they exist
        csv_dir = 'source_CSVs'
        if len(os.listdir(csv_dir)) > 0:
            print('---> The source_CSV directory contains the following csv files:')
            print('--->' + str(os.listdir(csv_dir)))
            print('You must delete them before continuing.')
            response = input(f"Do you want to delete all files in {csv_dir}? (Y/N): ")
            if response.lower() == "y":
                # loop through each file in the directory
                for file in os.listdir(csv_dir):
                    file_path = os.path.join(csv_dir, file)

                    # check if the file exists and is a file (not a directory)
                    if os.path.isfile(file_path):
                        # delete the file
                        os.remove(file_path)
                        print(f"{file_path} has been deleted.")
            else:
                print(f"---> You must delete the files in {csv_dir} before continuing.")
                quit()

        # export Excel worksheets to individual csv files
        # set the current working directory
        os.chdir('source_Excel')

        # find all Excel files in the current working directory
        excel_files = glob.glob('*.xlsx')

        # count the number of Excel files and check if there is > 1
        num_excel_files = len(excel_files)

        # check if there is more than one file
        if num_excel_files > 1:
            print('---> There can only be a single Excel file in the source_excel directory, but there are ' + str(num_excel_files))
            print('--->' + str(os.listdir()))
            print('---> You must delete all but one')
            quit()

        # get the base name of the first Excel file in the list (i.e., the file name without the directory path)
        excel_file_name = os.path.basename(excel_files[0])

        # initialize counter for CSV files
        csv_file_num = 1

        for sheet_name, df in pd.read_excel(excel_file_name, sheet_name=None).items():
            csv_file_name = f'{csv_file_num}_{sheet_name}.csv'
            df.to_csv(csv_file_name, index=False, encoding='utf-8')
            csv_file_num += 1

        # find all CSV files in the current working directory
        csv_files = glob.glob('*.csv')

        # move all CSV files to the new directory
        for csv_file in csv_files:
            csv_file_name = os.path.basename(csv_file)
            new_csv_file_path = os.path.join('../source_CSVs/', csv_file_name)
            os.rename(csv_file, new_csv_file_path)
        os.chdir('..')

    # option to use script simply to export Excel worksheets of a single file into separate csv files
    if only_for_csv_conversion == 'yes':
        print('--->  The following csv files have been created:')
        print(os.listdir('source_CSVs'))
        quit()

    # assign path
    path, dirs, files = next(os.walk("source_CSVs", topdown=True))
    file_count = len(files)
    # create empty list
    dataframes_list = []

    # append datasets to the list
    for i in range(file_count):
        files.sort()
        temp_df = pd.read_csv("./source_CSVs/" + files[i])
        temp_df.insert(0, 'plate_num', i + 1)
        dataframes_list.append(temp_df)

    # combine all dataframes
    cherry_samples = pd.concat(dataframes_list)

    # select and keep samples to cherrypick
    cherry_samples = (cherry_samples.loc[cherry_samples['cherrypick'] == 'yes'])

    # determine last sample if more than 96 samples
    if len(cherry_samples) > 191:
        last_sample = cherry_samples.iloc[192]
    else:
        last_sample = cherry_samples.iloc[len(cherry_samples) - 1]

    # determine length of dataframe
    cherry_length = len(cherry_samples)

    # insert correct number of cherrypick wells and remove cherrypick column
    cherry_samples.insert(2, 'cherry_well', wells[0:cherry_length])
    cherry_samples.insert(2, 'cherry_plate_num', cherry_plate_num[0:cherry_length])
    cherry_samples.drop('cherrypick', inplace=True, axis=1)

    # print number of samples selected and their wells
    print('---> ' + str(cherry_length) + ' samples selected for cherrypicking')
    print('---> See ' + base_name + '_cherrypicked.csv in output_files for new sample locations')
    print('---> Last sample on plate is:')
    print('')
    print(last_sample)

    # add column with amount of liquid
    cherry_samples['sample_vol'] = sample_vol

    # add row for blank well
    # blank_row = pd.DataFrame({'plate_num': [0], 'plate_well': ['NA'], 'cherry_well': ['H12'], 'sample_name': ['BLANK'], 'sample_vol': [10.0]})
    # cherry_samples = pd.concat([cherry_samples, blank_row], ignore_index=True)

    # add base_name to output file names
    outPlateName = base_name + '_cherrypicked.csv'

    # write files to output directory
    if not os.path.isdir('output_files'):
        os.mkdir('output_files')

    # write cherry samples to csv
    cherry_samples.to_csv('./output_files/' + outPlateName, index=False)

    # create dataframe for protocol

    # open DM-cherrypicking_protocol.py template and add values
    f = open("DM-cherrypicking_protocol.py")
    filedata = f.read()
    f.close()

    x = cherry_samples.to_string()
    newdata = filedata.replace('CHERRY_DATA', str(x))
    newdata = newdata.replace('plate_type_variable', plate_type)
    newdata = newdata.replace('tip_type_variable', tip_type)
    newdata = newdata.replace('sample_vol_variable', str(sample_vol))
    newdata = newdata.replace('Cherrypicking from .csv', base_name + ' Cherrypicking')

    f = open('output_files/' + base_name + '_cherrypicking_protocol.py', 'w')
    f.write(newdata)
    f.close()

    # simulate OT-2 run
    from opentrons.simulate import simulate, format_runlog

    # protocol name
    if simulate_run == 'yes':
        protocol_name = 'output_files/' + base_name + '_cherrypicking_protocol.py'
        # read the file
        protocol_file = open(protocol_name)
        # simulate() the protocol, keeping the runlog
        runlog, _bundle = simulate(protocol_file)
        # print the runlog
        print(format_runlog(runlog))