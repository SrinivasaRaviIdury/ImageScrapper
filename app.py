# doing necessary imports

import logging
import time
import pymongo
from selenium import webdriver
import requests
from flask import Flask, request, render_template
from flask_cors import cross_origin
import base64
import gunicorn
import os

app = Flask(__name__)  # initialising the flask app with the name 'app'


@app.route('/', methods=['GET'])  # route to display the home page
@cross_origin()
def homepage():
    return render_template("index.html")


@app.route('/img_view', methods=['POST', 'GET'])  # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        # obtaining the search string entered in the form
        searchString = request.form['content'].replace(" ", "").lower()
        # searchString = "audi"
        count = 1
        try:
            logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',
                                level=logging.INFO)
            logging.getLogger('urbanGUI')
            # mongodb: // localhost: 27017 /
            dbConn = pymongo.MongoClient(
                "mongodb+srv://<username>:<password>@srinivasaahlad.njxzl.mongodb.net/ImagecrawlerDB?retryWrites=true&w=majority")  # opening a connection to Mongo
            logging.info('Database Connection Success')
            db = dbConn['ImagecrawlerDB']  # connecting to the database called crawlerDB
            logging.info('connecting to the database called ImagecrawlerDB : Success')
            reviews = db[searchString].find({})
            images_lst = []
            if reviews.count() > 10:
                logging.info('Search For Database : Record Exists')
                for img in reviews:
                    images_lst.append(img["image"].decode('utf-8'))
                return render_template("ShowImage.html", images_lst=images_lst)
            else:
                lst_link = []
                image_url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={searchString}&oq={searchString}&gs_l=img"

                chrome_options = webdriver.ChromeOptions()
                chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")
                driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),
                                          chrome_options=chrome_options)
                driver.get(image_url)
                logging.info('Loaded Page')
                time.sleep(0.5)
                lst = driver.find_elements_by_css_selector(".rg_i.Q4LuWd")
                for ele in lst[:10]:
                    try:
                        ele.click()
                    except:
                        continue
                    for i in driver.find_elements_by_class_name("n3VNCb"):
                        if "http" in i.get_attribute("src") and len(lst_link) < 5:
                            lst_link.append(i.get_attribute("src"))
                # https://www.programcreek.com/2013/09/convert-image-to-string-in-python/
                try:
                    for link in lst_link:  # loop through links
                        try:
                            img = requests.get(link).content
                        except:
                            continue
                        string = base64.b64encode(img)
                        doc = db[searchString]
                        doc.insert_one({"name": searchString + str(count), 'image': string})
                        images_lst.append(string.decode('utf-8'))
                        count += 1
                    return render_template("ShowImage.html", images_lst=images_lst)
                except Exception as e:
                    print(e)
                driver.close()
        except Exception as e:
            print(e)
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
