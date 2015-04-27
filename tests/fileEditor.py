__author__ = 'patrickbelon'
import datetime as dt
import time
import uuid
import os
import signal
import shutil
import sys

# Purpose: Create edit and delete files to test FileWatcher
# Randomly delete edit, modify, create files.
generated_files = []


def signal_term_handler(sig, frame):
    clean_up()


# delete a random file
def delete_file():
    print 'Trying to delete file'
    if generated_files.__len__() > 0:
        rand_index = randint(0, generated_files.__len__()-1)
        file_name = generated_files[rand_index]
        os.remove(file_name)
        generated_files.remove(file_name)
        print 'Rand to delete '+file_name


# create a file with a random name
def create_file():
    file_name = '../modules/'+uuid.uuid4().__str__() + '.py'
    print 'Creating file ' + file_name
    file_object = open(file_name, 'w+')
    generated_files.append(file_name)
    shutil.copy("../modules/Tester.py", file_name)
    # with open("./DatabaseModule.py", "r") as template_object:
    #     for line in template_object:
    #         file_object.write(line)


# Take a random file in list and append garbage to it
def modify_file():
    print 'Trying to modify file'
    if generated_files.__len__() > 0:
        rand_index = randint(0, generated_files.__len__()-1)
        file_object = open(generated_files[rand_index], 'a+')
        file_object.write("\n")


def move_file():
    file_name = uuid.uuid4().__str__() + '.py'
    print 'Creating file for move' + file_name
    open(file_name, 'w+')
    shutil.copy("../modules/Tester.py", file_name)
    time.sleep(.5)
    shutil.move(file_name, "../modules/"+file_name)
    print 'moved file ' + file_name + 'to ' + "../modules/"+file_name
    generated_files.append("../modules/"+file_name)


# Take all files and erase them to
def clean_up():
    print 'clean up'
    for file_name in generated_files:
        os.remove(file_name)
        print 'removed ' + file_name
    os.system("rm ../modules/*.pyc")

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_term_handler)
    from random import randint
    option = sys.argv[1] if len(sys.argv) > 1 else 1
    if option == '1':
        run_time = dt.datetime.now()
        run = True
        options = {0: delete_file,
                   1: create_file,
                   2: modify_file,
                   3: move_file,
                   }
        try:
            while run:
                action = randint(0, 3)
                print action
                options[action]()
                seconds_elapsed = dt.datetime.now() - run_time
                if seconds_elapsed.total_seconds() > 100:
                    run = False
                time.sleep(.1)
        except KeyboardInterrupt:
            clean_up()
        clean_up()
    elif option == '2':
        run_time = dt.datetime.now()
        run = True
        try:
            while run:
                create_file()
                time.sleep(.5)
                #delete_file()
                seconds_elapsed = dt.datetime.now() - run_time
                if seconds_elapsed.total_seconds() > 100:
                    run = False
        except KeyboardInterrupt:
            clean_up()
        clean_up()
    elif option == '3':
        try:
            while True:
                move_file()
                delete_file()
                time.sleep(.5)
        except:
            pass
        finally:
            clean_up()