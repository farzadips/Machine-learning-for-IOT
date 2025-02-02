import cherrypy
import json
from functools import reduce
import base64

from more_itertools import only
from tenacity import retry
import tensorflow as tf
import numpy as np
import time


class Calculator(object):
    exposed = True

    def GET(self, *path, **query):
        from os import listdir
        from os.path import isfile, join
        print(str(path[0]) )
        if path[0] == 'list':
            onlyfiles = [f for f in listdir('E:\Github\Machine-learning-for-IOT\Homework3\ex1\part 1\models') if isfile(join('E:\Github\Machine-learning-for-IOT\Homework3\ex1\part 1\models', f))]
            print(onlyfiles)
            output = {'path': onlyfiles}
            output_json = json.dumps(output)

            #return onlyfiles
            return output_json
        elif path[0] == 'predict':
            model_name = query.get('m')
            th = float(query.get('th'))
            tt = float(query.get('hh'))
            model_path = 'E:/Github/Machine-learning-for-IOT/Homework3/ex1/part 1/models/' + model_name
            interpreter = tf.lite.Interpreter(model_path)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            input_shape = input_details[0]['shape']
            temp_hum_set = np.array([[]],dtype=np.float32)
            first = True
            window = np.zeros([1, 6, 2], dtype=np.float32)
            expected = np.zeros(2, dtype=np.float32)

            MEAN = np.array([9.107597, 75.904076], dtype=np.float32)
            STD = np.array([ 8.654227, 16.557089], dtype=np.float32)
            while(True):
                if(first):
                    temp_hum_set = np.array([[-8.2, 93.3]],dtype=np.float32)
                    first = False
                else:
                #np.array([[[-8.2, 93.3],[-8.41, 93.4],[-8.51, 93.90],[-8.31, 94.2],[-8.27, 94.1],[-8.05, 94.4],[-7.62, 94.8]]],dtype=np.float32)
                    temp_hum_set = np.append(temp_hum_set,[[-8.2, 93.3]], axis = 0)
                
                if(temp_hum_set.shape[0]>6):
                    print("predicting")
                    for i in range(7):
                        
                        temperature = temp_hum_set[i][0]
                        humidity = temp_hum_set[i][1]
                        if i < 6:
                            window[0, i, 0] = np.float32(temperature)
                            window[0, i, 1] = np.float32(humidity)
                        if i == 6:
                            expected[0] = np.float32(temperature)
                            expected[1] = np.float32(humidity)

                            window = (window - MEAN) / STD
                            interpreter.set_tensor(input_details[0]['index'], window)
                            interpreter.invoke()
                            predicted = interpreter.get_tensor(output_details[0]['index'])
                            temp_hum_set = temp_hum_set[1:]
                            if(abs(predicted[0][0][0]-expected[0])>tt):
                                error_text = 'Temperature Alert: Predicted=' + str(predicted[0][0][0]) + '°C Actual=' + str(expected[0]) + '°C'
                                output = {
                                            'result': error_text,
                                        }
                                output_json = json.dumps(output)
                                return output_json
                            if(abs(predicted[0][0][1]-expected[1])>th):
                                error_text = 'Humidity Alert: Predicted=' + str(predicted[0][0][1]) + '% Actual=' + str(expected[1]) + '%'
                                output = {
                                            'result': error_text,
                                        }
                                output_json = json.dumps(output)
                                return output_json
                            # temp_hum_set = temp_hum_set[1:]
                            # print('Measured: {:.1f},{:.1f}'.format(expected[0], expected[1]))
                            # print('Predicted: {:.1f},{:.1f}'.format(predicted[0, 0],
                            #     predicted[0, 1]))
                    break

                #time.sleep(1)


        #time.sleep(0.2)

            return






    def POST(self, *path, **query):
        pass

    def PUT(self, *path, **query):
        print("recieved")
        if len(path) < 0:
            raise cherrypy.HTTPError(400, 'Wrong path')

        if len(query) > 0:
            raise cherrypy.HTTPError(400, 'Wrong query')
        
        if(path[0] == "add"):

            body = cherrypy.request.body.read()
            body = json.loads(body)

            name = body['mn']
            events = body['e']
            for event in events:
                    model_string = event['vd'] 
            model_bytes = base64.b64decode(model_string)


            tflite_model_dir = "E:/Github/Machine-learning-for-IOT/Homework3/ex1/part 1/models/" + name
            with open(tflite_model_dir, 'wb') as fp:
                fp.write(model_bytes)
            output = {
                        'result': "done",
                    }
            output_json = json.dumps(output)
            return output_json

    def DELETE(self, *path, **query):
        pass


if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    cherrypy.tree.mount(Calculator(), '', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.engine.start()
    cherrypy.engine.block()
