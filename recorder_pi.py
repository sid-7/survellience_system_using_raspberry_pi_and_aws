from threading import Thread
from picamera import PiCamera
import os, datetime, threading, subprocess, boto3, multiprocessing, time, os
from time import sleep
import RPi.GPIO as GPIO

def subprocess_cmd(command):
	process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	proc_stdout = process.communicate()[0].strip()

def parse_output(file_name):
	objects = set()
	with open(file_name, "r") as f:
		lines = f.readlines()
		for line in lines:
			line = line.split("%")
			if(len(line)==2):
				objects.add(line[0].split(":")[0])
	with open(file_name, "w") as f:
		if(len(objects)==0):
			f.write("No Objects Detected")
		else:
			f.write(str(list(objects)))
	#print("-"*10,"File {} updated {} ".format(file_name, list(objects)))

def upload_result(output_file):
	global s3_client, bucket_name
	#print("Uploading result: {}".format(output_file))
	parse_output(output_file)
	s3_client.upload_file(output_file, bucket_name, "output/{}".format(output_file))
	shared['local_videos'] -= 1

def process_video(file_name):
	shared["processor_flag"] = True
	#print("IN Process", file_name)
	output_file_name = file_name.split(".")[0]
	cmd = "xvfb-run ./darknet detector demo cfg/coco.data cfg/yolov3-tiny.cfg yolov3-tiny.weights " + file_name + " > "  + output_file_name + " 2>"+file_name+"_err.txt"
	start = datetime.datetime.now()
	os.system(cmd)
	end = datetime.datetime.now()
	sleep(5)
	shared["processor_flag"] = False
	return output_file_name


def send_video_to_local_processor(shared, file_name):
	global bucket_name, s3_client, output_threads
	#print("(Local Procesor): {} uploading".format(file_name))
	s3_client.upload_file(file_name, bucket_name, file_name)
	output_file = process_video(file_name)
	shared['Output_Queue_threads'] = shared['Output_Queue_threads'] + [output_file]


def send_video_to_master(file_name):
	global bucket_name, s3_client, sqs_resource
	s3_client.upload_file(file_name, bucket_name, file_name)
	#print("(MASTER): {} UPLOADED".format(file_name))	
	input_queue = sqs_resource.get_queue_by_name(QueueName = "Input_Queue")
	response = input_queue.send_message(MessageBody=file_name)

def input_queue_polling(shared):
	global s3_client, sqs_resource, bucket_name, output_threads
	while(sqs_resource.get_queue_by_name(QueueName="Input_Queue").attributes['ApproximateNumberOfMessages']!='0'):
		message = sqs_resource.get_queue_by_name(QueueName="Input_Queue").receive_messages()
		if(len(message)==0):
			continue
		shared['local_videos'] += 1
		file_name = message[0].body
		message[0].delete()
		output_file = process_video(file_name)
		shared['Output_Queue_threads'] =  shared['Output_Queue_threads'] + [output_file]
	shared['processor_flag'] = False

def record_video(shared):
	total_time, partitions = 5, 1
	i_=1
	time_per_split = total_time/partitions
	threads = []

	sensor =18
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(sensor, GPIO.IN)		
	on, off, flag = 0, 0, 0
	
	while shared['record']:
		i=GPIO.input(sensor)
		if(i==1): # motion detected
			camera = PiCamera()
			#print("(Record Videos): Starting stream {}.".format(i_))
			now = datetime.datetime.now()
			timestamp = now.strftime("%y-%m-%d_%H-%M-%S")
			print("(Record Videos): Starting stream {}-{}.".format(i_, timestamp))
			i_ += 1
			file_name_ = "video-{}.h264".format(timestamp)
	
			camera.start_recording(file_name_)
			sleep(time_per_split)
			camera.stop_recording()
	
			if shared['processor_flag'] == True:
				t = threading.Thread(target=send_video_to_master, args=(file_name_,))
				threads.append(t)
				t.start()
			else:
				shared['local_videos'] += 1
				t = threading.Thread(target=send_video_to_local_processor, args=(shared,file_name_,))
				threads.append(t)
				t.start()
			camera.close()
		else:
			sleep(0.1)

	print("(Record Videos): Stop stream.")
	print("(Record Videos): Waiting for all threads({}) to complete execution.".format(len(threads)))
	for thread in threads:
		thread.join()
	#camera.close()
	#sending signal to master
	print("(Record Videos): All threads collected")
	input_queue = sqs_resource.get_queue_by_name(QueueName = "Output_Queue")
	response = input_queue.send_message(MessageBody="no more messages")
	print("Message sent to master to StOp")
	print("IP Q Polling START")
	input_queue_polling(shared)
	print("IP Q polling stopped")

if __name__=='__main__':
	st = datetime.datetime.now()
	global s3_client, sqs_resource,ec2_client, bucket_name, total_time, partitions, master_id, output_threads

	output_threads = []
	master_id = "i-0d420f853783ff495"
	total_time = 5
	partitions = 1


	with multiprocessing.Manager() as manager:
		shared = manager.dict()
		
		ec2_client = boto3.client('ec2')
		s3_client = boto3.client('s3')
		sqs_resource = boto3.resource('sqs')
		bucket_name = 'bucket23797'

		shared['Output_Queue_threads']=[]
		shared['processor_flag']=False
		shared['local_videos'] = 0

		p3 = multiprocessing.Process(target = record_video, args=(shared,))
		shared['output_polling'] = True
		shared['record'] = True
		p3.start()
		input("Press Enter to stop recording: \n")
		print("Stopping recording")
		shared['record'] = False
		p3.join()
		shared['output_polling']=False
		print("Waiting for upload threads to stop")
		for output_file in shared['Output_Queue_threads']:
			t = Thread(target=upload_result, args=(output_file,))
			t.start()
			output_threads.append(t)
		for thread in output_threads:
			thread.join()
