#Developed by Magnus Berg, 2023 for the University of Toronto, Mississauga Digital Scholarship Unit
#Are you telling me a TRANS coded this film?

import os
import FreeSimpleGUI as sg
import shutil
import subprocess
import time
import pdb
import ffmpeg
import threading
import multiprocessing
import bagit
import sys

sg.theme('Reddit')

#Sets what the GUI will look like/have as inputs 

def collapse(layout, key, visible):
	return sg.pin(sg.Column(layout, key=key, visible=visible))

fourtrack_expand = [
			[sg.Text('Select the third MXF audio file [ex. "C0001A03.MXF"]', size=(39, 1)), sg.Input(key='-audio3-'), sg.FileBrowse()],
			[sg.Text('Select the fourth MXF audio file [ex. "C0001A04.MXF"]', size=(39, 1)), sg.Input(key='-audio4-'), sg.FileBrowse()]]


layout = [[sg.Text('XDCam Converter and Digital Preservation Packager', font=("bold", 20))],
	 [sg.Text('Select the MXF video file [ex."C0001V01.MXF"]', size=(40, 1)), sg.Input(key='-video-'), sg.FileBrowse()],
         [sg.Text('Select the first MXF audio file [ex."C0001A01.MXF"]', size=(40, 1)), sg.Input(key='-audio1-'), sg.FileBrowse()],
	 [sg.Text('Select the second MXF audio file [ex."C0001A02.MXF"]', size=(40, 1)), sg.Input(key='-audio2-'), sg.FileBrowse()],
	 [sg.Button('Add 4-channel audio', key='-4channel-', enable_events=True)],
	[collapse(fourtrack_expand, '-fourtrack_expand-', False)],
	[sg.Text('Select the directory you want to export the files to', size=(40, 1)), sg.Input(key='-dir-'), sg.FolderBrowse()],
	[sg.Text('What is the filename for the files?', size=(40, 1)), sg.InputText(key='-filename-')],
         [sg.Submit(), sg.Cancel(), sg.Button('Reset', key='-reset-')], 
	[sg.Multiline(size=(100, 5), key='-multiline-', autoscroll=True, visible=True, expand_y=True)],
	[sg.ProgressBar(100, orientation='h', expand_x=True, size=(3, 20),  key='-PBAR-', visible=False)]]
	

window = sg.Window('XDCAM Converter', layout, resizable=True).Finalize()
progress_bar = window.find_element('-PBAR-')
reset = window.find_element('-reset-')

def input_check(video_stream, audio_channel1, audio_channel2, user_filename, main_dir):	

#Checks that the user supplied all files, an output directory and filename
	if video_stream and audio_channel1 and audio_channel2 and user_filename and main_dir:
		process0 = True
		
#Checks to see if a video stream, two audio streams, filename, and output directory are present. If they are not, alerts the user to add them and try again.
	elif bool(video_stream) == False:
		process0 = False

	elif bool(audio_channel1) == False:
		process0 = False

	elif bool(audio_channel2) == False:
		process0 = False

	elif bool(user_filename) == False:
		process0 = False

	elif bool(main_dir) == False:
		process0 = False
		
	return process0


def ori_dir_check(main_dir, original_dir):
#Makes the originals directory
	try:
		original_dir_prep = os.mkdir(original_dir)
	except:
		process1 = False
	else:
		process1 = True
	
	return process1

def mas_dir_check(main_dir, master_dir):
#Makes the master directory
	try:
		master_dir_prep = os.mkdir(master_dir)
	except:
		process2 = False
	else:
		process2 = True
	
	return process2

def acc_dir_check(main_dir, access_dir):
#Makes the access directory
	try:
		access_dir_prep = os.mkdir(access_dir)
	except:
		process3 = False
	else:
		process3 = True

	return process3

def mxf_combine_2(main_dir, video_stream, audio_channel1, audio_channel2, mxf_output_name, mxf_log):		
#combine audio and video MXF files. Copies video stream and creates stereo audio track out of two audio files
	combine_mxf_str = r'ffmpeg -i ' + str(video_stream) + ' -i ' + str(audio_channel1) + ' -i ' + str(audio_channel2) + ' -c:v copy -copyts -filter_complex "[1:a][2:a]join=2:stereo:0.0-FL|1.0-FR[aout]" -map 0:v -map "[aout]" -y -loglevel error ' + str(mxf_output_name) 

	mxf_process=subprocess.run(combine_mxf_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
	mxf_process.stdout = open(mxf_log, 'w')
	return mxf_process.returncode

def mxf_combine_4(main_dir, video_stream, audio_channel1, audio_channel2, audio_channel3, audio_channel4, mxf_output_name, mxf_log):	
#combine audio and video MXF files. Copies video stream and creates stereo audio track out of four audio files
	combine_mxf_str = r'ffmpeg -i ' + str(video_stream) + ' -i ' + str(audio_channel1) + ' -i ' + str(audio_channel2) + ' -i ' + str(audio_channel3) + ' -i ' + str(audio_channel4) + ' -c:v copy -copyts -filter_complex "[1:a][2:a][3:a][4:a]amerge=inputs=4, pan=stereo|FL<c0+0.75*c1+0.25*c2|FR<0.25*c1+0.75*c2+c3[aout]" -map 0:v -map "[aout]" -y -loglevel error ' + str(mxf_output_name) 

	mxf_process=subprocess.run(combine_mxf_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
	mxf_process.stdout = open(mxf_log, 'w')
	return mxf_process.returncode

def create_master(master_dir, master_file_name, user_filename, mxf_output_name, master_log):
#creates a master file (ffv1 mkv) and md5 checksum file based on the temporary mxf
	master_md5 = os.path.join(master_dir, user_filename+'.md5')
	master_file_str = r'ffmpeg -i ' + str(mxf_output_name) + ' -dn -c:v ffv1 -level 3 -g 1 -slicecrc 1 -slices 9 -copyts -vf "yadif, format=yuv422p" -c:a copy -loglevel error ' + str(master_file_name) + ' -f framemd5 -an ' + str(master_md5) 

	master_file = subprocess.run(master_file_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	master_file.stdout = open(master_log, 'w')
	return master_file.returncode

def create_access(access_dir, access_file_name, mxf_output_name, access_log):
#creates an access file (mp4) based on the temporary mxf
	access_file_str = r'ffmpeg -i ' + str(mxf_output_name) + ' -c:v libx264 -copyts -filter:v "yadif, scale=1440:1080:flags=lanczos, pad=1920:1080:(ow-iw)/2:(oh-ih)/2, format=yuv422p" -crf 28 -movflags +faststart -loglevel error ' + str(access_file_name)	

	access_file = subprocess.run(access_file_str, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	access_file.stdout = open(access_log, 'w')
	return access_file.returncode

def bag_files(main_dir):
#bags all files based on the Library of Congress's Bagit standard (including assigning checksums)
	bagstr = str(main_dir)
			
	try:
		bagit.make_bag(bagstr, {'Contact-Name': 'XDCAM Conversion Applet'})
	except:
		failure=True
	else:
		failure=False
	return failure


def the_gui():
	open = False
	while True:
		event, values = window.read()
		if event.startswith('-4channel-'):
			open = not open
			window['-fourtrack_expand-'].update(visible=open)
			#window.size(800,500)
		if event == 'Submit':
			video_stream = values['-video-']
			audio_channel1 = values['-audio1-']
			audio_channel2 = values['-audio2-']
			audio_channel3 = values['-audio3-']
			audio_channel4 = values['-audio4-']
			user_filename = values['-filename-']
			main_dir = values['-dir-']

			status1 = input_check(video_stream, audio_channel1, audio_channel2, user_filename, main_dir)

			if status1==False:
				window['-multiline-'].update('All fields must be complete in order to continue. Please try again.'+'\n', append=True)
				status=False
			
			else: 
				window['-multiline-'].update('Files added to queue'+'\n', append=True)
				access_dir = os.path.join(main_dir, 'Access')
				master_dir = os.path.join(main_dir, 'Master')
				original_dir = os.path.join(main_dir, 'Originals')
				status2 = ori_dir_check(main_dir, original_dir)
		
				if status2==False:
					window['-multiline-'].update('Unable to continue conversion process. Ensure that no duplicate directories exist and try again.'+'\n', append=True)
					status3=False
			
				else:
					window['-multiline-'].update('Created Original directory'+'\n', append=True)
					status3=mas_dir_check(main_dir, master_dir)

					if status3==False:
						window['-multiline-'].update('Unable to continue conversion process. Ensure that no duplicate directories exist and try again.'+'\n', append=True)
						status3=False
					else:
						window['-multiline-'].update('Created Master directory'+'\n', append=True)
						status4=acc_dir_check(main_dir, access_dir)
					
						if status4==False:
							window['-multiline-'].update('Unable to continue conversion process. Ensure that no duplicate directories exist and try again.'+'\n', append=True)
							status5=False
						else:
							window['-multiline-'].update('Created Access directory'+'\n', append=True)
							status5=True

			if status5:
				access_file_name = os.path.join(access_dir, user_filename+'.mp4')
				master_file_name = os.path.join(master_dir, user_filename+'.mkv')
				mxf_output_name = os.path.join(main_dir, 'temp_concat.mxf')
				mxf_log = os.path.join(main_dir, "ffreport.log")
				master_log = os.path.join(master_dir, "ffreport.log")
				access_log = os.path.join(access_dir, "ffreport.log")

				window['-multiline-'].update('Attempting MXF concatenation. Please wait.'+'\n', append=True)
				progress_bar.update(visible=True)
				progress_bar.UpdateBar(0, 5)
				
				if bool(audio_channel3) == False and bool(audio_channel4) == False:
					window.perform_long_operation(lambda: mxf_combine_2(main_dir, video_stream, audio_channel1, audio_channel2, mxf_output_name, mxf_log), '-MXF Complete-')
				elif bool(audio_channel3) == True and bool(audio_channel4) == True:
					window.perform_long_operation(lambda: mxf_combine_4(main_dir, video_stream, audio_channel1, audio_channel2, audio_channel3, audio_channel4, mxf_output_name, mxf_log), '-MXF Complete-')
				else:
					window['-multiline-'].update('Error. Audio channel configuration is wrong. Please attach all relevant audio channels.'+'\n', append=True)
				
		
		elif event == '-MXF Complete-':
			status6={values[event]}
			if status6=={0}:
				if os.path.getsize(mxf_log) == 0:
					os.remove(mxf_log)
					window['-multiline-'].update('Completed MXF concatenation'+'\n', append=True)
					window['-multiline-'].update('Attempting master file creation. Please wait.'+'\n', append=True)	
					progress_bar.UpdateBar(1, 5)
					window.perform_long_operation(lambda: create_master(master_dir, master_file_name, user_filename, mxf_output_name, master_log), '-Master Complete-')
				else:
					window['-multiline-'].update('MXF concatenation failed. Please see log file.'+'\n', append=True)	
					window.write_event_value('-failure-', True)
			else:
				window.write_event_value('-failure-', True)	
		elif event == '-Master Complete-':
			status7={values[event]}
			if status7=={0}:
				if os.path.getsize(master_log) == 0:
					os.remove(master_log)
					window['-multiline-'].update('Derived new master file.'+'\n', append=True)
					window['-multiline-'].update('Attempting access file creation. Please wait.'+'\n', append=True)
					progress_bar.UpdateBar(2, 5)
					window.perform_long_operation(lambda: create_access(access_dir, access_file_name, mxf_output_name, access_log), '-Access Complete-')
				else:
					window['-multiline-'].update('Master file creation failed. Please see log file.'+'\n', append=True)	
					window.write_event_value('-failure-', True)
			else:
				window.write_event_value('-failure-', True)
		elif event == '-Access Complete-':
			status8={values[event]}	
			if status8=={0}:
				if os.path.getsize(access_log) == 0:
					os.remove(access_log)
					window['-multiline-'].update('Derived new access file.'+'\n', append=True)
					window['-multiline-'].update('Attempting to remove temp file. Please wait.'+'\n', append=True)
				
					try:
						os.remove(mxf_output_name)
					except:
						window['-multiline-'].update('Error occurred. Unable to remove temp MXF file.'+'\n', append=True)
						window.write_event_value('-failure-', True)
					else:
						window['-multiline-'].update('Removed temp MXF file'+'\n', append=True)
						window['-multiline-'].update('Attempting to move files into appropriate directories. Please wait.'+'\n', append=True)
						progress_bar.UpdateBar(3, 5)
					
						try:
							move_gen_prep = os.path.join(main_dir, 'General')
							move_PROAV_prep = os.path.join(main_dir, 'PROAV')
							move_gen = shutil.move(move_gen_prep, original_dir)
							move_PROAV = shutil.move(move_PROAV_prep, original_dir)
						except:
							window['-multiline-'].update('Error occurred. Unable to move files into appropriate directories.'+'\n', append=True)
							window.write_event_value('-failure-', True)
	
						else: 
							window['-multiline-'].update('Moved original files to Originals directory'+'\n', append=True)
							window['-multiline-'].update('Attempting to bag files. Please wait.'+'\n', append=True)
							progress_bar.UpdateBar(4, 5)
							status9=bag_files(main_dir)
							if status9:
								window.write_event_value('-failure-', True)
							elif status9==False:
								window.write_event_value('-failure-', False)
				else:
					window['-multiline-'].update('Access file creation failed. Please see log file.'+'\n', append=True)	
					window.write_event_value('-failure-', True)
			
			else:
				window.write_event_value('-failure-', True)

		elif event== '-failure-':
			failure=values['-failure-']
			if failure==True:
				window['-multiline-'].update('One or more processes have failed. Unable to continue.'+'\n', append=True)
				progress_bar.update(bar_color=('red'))
			elif failure==False:
				window['-multiline-'].update('XDCAM conversion and bagging process is complete.'+'\n', append=True)
				progress_bar.UpdateBar(5, 5)
		
		elif event == '-reset-':
			progress_bar.update(visible=False)
			window['-multiline-'].update('')
			window.find_element('-video-').update('')
			window.find_element('-audio1-').update('')
			window.find_element('-audio2-').update('')
			window.find_element('-filename-').update('')
			window.find_element('-dir-').update('')
			window.find_element('-audio3-').update('')
			window.find_element('-audio4-').update('')
			
		elif event == sg.WIN_CLOSED or event == 'Cancel':
			break
			window.close()


if __name__=='__main__':
	the_gui()
