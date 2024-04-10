from kivy.core.text import LabelBase
from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.uix.camera import Camera
from kivy.lang import Builder
from kivy.core.window import Window
import pandas as pd
import cv2
from PIL import Image as PILImage
import tempfile
import requests

Window.size = (310, 580)

class CameraScreen(Screen):
    pass

class TreatmentScreen(Screen):
    pass

PREDICTION_API_URL = "https://cnn-model-api-deployment-ac2b40fcf26d.herokuapp.com/predict"

class Dtreaty(MDApp):
    condition_value = StringProperty()  # Define a StringProperty
    treatment = StringProperty()
    weather_info = StringProperty()
    weather_info_desc = StringProperty()
    def build(self):
        screenmanager = ScreenManager()
        screenmanager.add_widget(Builder.load_file("main.kv"))
        screenmanager.add_widget(Builder.load_file("camera.kv"))
        screenmanager.add_widget(Builder.load_file("treatment.kv"))
        return screenmanager
    
    def capture_image(self):
        current_screen = self.root.current_screen
        if current_screen.name == 'camera':
            camera_widget = current_screen.ids.camera_id
            if camera_widget.texture:
                img_texture = camera_widget.texture
                if img_texture:
                    pil_image = PILImage.frombytes('RGBA', img_texture.size, img_texture.pixels)
                    pil_image = pil_image.convert('RGB')
                    pil_image = pil_image.resize((256, 256)) 

# The API integration Code

                    # Save the image to a temporary file
                    temp_image_path = tempfile.NamedTemporaryFile(suffix=".jpg").name
                    pil_image.save(temp_image_path)

                    # Send the image to FastAPI for prediction
                    files = {'file': open(temp_image_path, 'rb')}
                    response = requests.post(PREDICTION_API_URL, files=files)
                    if response.status_code == 200:
                        prediction_data = response.json()
                        predicted_class_name = prediction_data.get('class', 'Unknown')
                        confidence = prediction_data.get('confidence', 0)
                        if confidence >= 0.60:
                            self.label = f"{predicted_class_name}"
                    else:
                        self.label = "Please Try Again..."

    def read_data(self):
        df = pd.read_csv('treatment-book.csv', encoding='ISO-8859-1')
        condition_column = 'disease_name' 
        condition_value = self.label
        value_column = 'treatment'
        self.no_data = "No matching data found"

        self.condition_value = condition_value

        self.treatment_series = df.loc[df[str(condition_column)] == str(condition_value), str(value_column)]
        self.treatment_series = self.treatment_series.astype(str)
        treatment = "\n".join(self.treatment_series) if not self.treatment_series.empty else self.no_data

        self.treatment = treatment
    
    def fetch_weather(self):
        # city_name = "London"
        api_key = '432a8658a6991c2c948f1125de99c13d'
        url = f'https://api.openweathermap.org/data/3.0/onecall?lat=35.92&lon=74.30&appid={api_key}'
        
        try:
            response = requests.get(url)
            data = response.json()
            current_weather = data['current']
            # Assuming temperature is in Kelvin
            temperature_kelvin = current_weather['temp']
            # Convert temperatures to Celsius
            temperature_celsius = temperature_kelvin - 273.15

            # Update the weather_info string to include Celsius temperatures
            weather_info = "\n"
            weather_info += f"{temperature_celsius:.2f} °C"
            
            weather_info_desc = "\n"
            weather_info_desc += f"Description: {current_weather['weather'][0]['description']}\n"

            self.weather_info = weather_info
            self.weather_info_desc = weather_info_desc

            print(weather_info_desc)

        except Exception as e:
            self.weather_info = "Please Connect To Internet"

    def get_weather_image(self, weather_info_desc):
        if 'broken clouds' or 'scattered clouds' in weather_info_desc.lower():
            return'images/sunny-cloud.png'
        elif 'overcast clouds'in weather_info_desc.lower():
            return 'images/cloudy.png'
        elif 'clear'in weather_info_desc.lower():
            return 'images/sun.png'
        else:
            return 'images/sun-cloudy-rain.png'

if __name__ == "__main__":
    LabelBase.register(name="Poppins", fn_regular="Poppins-Bold.ttf")
    LabelBase.register(name="Poppinsl", fn_regular="Poppins-Light.ttf")

    Dtreaty().run()