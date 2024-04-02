import argparse

from nnunet.paths import default_plans_identifier

from data_setup import setup_data

def main(brats_pardir, task_num, task_name):
    """
    Generates symlinks to be used for NNUnet training, assuming we already have a 
    dataset on file coming from BraTS22 samples.

    Also creates the json file for the data, as well as runs nnunet preprocessing.

    should be run using a virtual environment that has nnunet version 1 installed.
    NOTE: The environmental variables: 
          nnUNet_raw_data_base="/raid/edwardsb/projects/RANO/BraTS22_pretending_tobe_postopp/nnUNet_raw_data_base" AND
          nnUNet_preprocessed="/raid/edwardsb/projects/RANO/BraTS22_pretending_tobe_postopp/nnUNet_raw_data_base/nnUNet_preprocessed"

    args:
    brats_pardir(str)     : Parent directory for postopp data.  
                                    Should have subdirectories with structure:
                                    │   ├── Subject1
                                    │   │   ├── 'Subject1_t1.nii.gz',
                                    |   |   |---'Subject1_t2.nii.gz',
                                    |   |   |---'Subject1_t1ce.nii.gz',
                                    |   |   |---'Subject1_flair.nii.gz'
                                    |   |-- Subject2
                                    |   |   |---Subj...
                                    |   | .
                                    |   | .

    task_num(str)                   : Should start with '5'. 
    task_name(str)                  : Name of task that is part of the task name
    """

    # some argument inspection
    task_digit_length = len(str(task_num))
    if task_digit_length != 3:
         raise ValueError(f'The number of digits in {task_num} should be 3, but it is: {task_digit_length} instead.')
    if str(task_num)[0] != '5':
         raise ValueError(f"The three digit task number: {task_num} should start with 5 to avoid NNUnet repository tasks, but it starts with {task_num[0]}")    
    setup_data(brats_pardir=brats_pardir, task_num=task_num, task_name=task_name)


if __name__ == '__main__':

        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            '--brats_pardir',
            type=str,
            help="Parent directory to BraTS22 data.")
        argparser.add_argument(
            '--task_num',
            type=int,
            help="Should start with '5'. If fedsim == N, all N task numbers starting with this number will be used.")
        argparser.add_argument(
            '--task_name',
            type=str,
            help="Part of the NNUnet data task directory name. With 'first_three_digit_task_num being 'XXX', the directory name becomes: .../nnUNet_raw_data_base/nnUNet_raw_data/TaskXXX_<task_name>.")
        
        args = argparser.parse_args()

        kwargs = vars(args)

        main(**kwargs)
