"""
Last Update: 03/09/2023
Author: Hanting Li

This scraper automatically extracts today's breakfast,
lunch, and dinner menus, for Anteatery and Brandywine,
and stores data in our Firestore database.
"""

import time
from bs4 import BeautifulSoup
from selenium import webdriver
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from selenium.webdriver import Keys

cred = credentials.Certificate('cs125-wellness-advisor-firebase-adminsdk-v399r-62786f9c7b.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

meals = ['Breakfast', 'Lunch', 'Dinner']


def delete_collection(coll_ref, batch_size):
    docs = coll_ref.list_documents(page_size=batch_size)
    deleted = 0

    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.get().to_dict()}')
        doc.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


if __name__ == '__main__':
    print("Hello scraper!")
    url_ant = 'https://uci.campusdish.com/LocationsAndMenus/TheAnteatery'
    url_bw = 'https://uci.campusdish.com/LocationsAndMenus/Brandywine'

    dinings = {'Anteatery': url_ant, 'Brandywine': url_bw}

    for dining in dinings:
        url = dinings[dining]

        for meal in meals:

            driver = webdriver.Edge(r"msedgedriver.exe")
            driver.get(url)

            # Wait for the dynamic content to load
            driver.implicitly_wait(3)
            x = '//*[@id="onetrust-close-btn-container"]/button'
            x2 = '//*[@id="modal-root-mail-subsription"]/div/div/div/div/div/div[1]/button'
            change_xpath = """//*[@id="react_menus"]/nav/div[2]/div[1]/div/button/div"""
            current_meal_xpath = '//*[@id="react-select-2-input"]'

            driver.find_element("xpath", x).click()
            driver.implicitly_wait(2)
            driver.find_element("xpath", x2).click()
            driver.implicitly_wait(5)
            time.sleep(2)
            button = driver.find_element("xpath", change_xpath)
            time.sleep(5)
            driver.implicitly_wait(5)
            button.click()
            driver.implicitly_wait(2)
            sendKey = driver.find_element("xpath", current_meal_xpath)
            time.sleep(2)
            sendKey.send_keys(meal)
            time.sleep(2)
            sendKey.send_keys(Keys.ENTER)
            time.sleep(4)
            done_button = """//*[@id="modal-root"]/div/div/div/div/div[3]/button[2]/span"""
            driver.find_element("xpath", done_button).click()
            driver.implicitly_wait(3)
            time.sleep(3)

            dynamic_content = driver.page_source

            collection_ref = db.collection(dining+'_'+meal)

            # parse html string
            soup = BeautifulSoup(dynamic_content, 'lxml')
            category = soup.find_all('div', {'class': 'sc-tQuYZ gvgoZc'})
            print(dining+" "+meal+": " + str(len(category)) + " items.")
            print()

            for item in category:
                name = item.find('h3')
                calorie = item.find('span', {'class': 'sc-djUGQo cBzVIR ItemCalories'})
                if calorie:
                    print("Name: " + str(name.text))
                    print("Calorie: ", calorie.text)

                    doc_ref = collection_ref.document(str(name.text))
                    doc_ref.set({
                        'name': str(name.text),
                        'calorie': int(calorie.text.split()[0]),
                        'time': meal
                    })
                else:
                    print("Name: ", name.text)
                    print("Calorie: 0 Calories")

                    doc_ref = collection_ref.document(str(name.text))
                    doc_ref.set({
                        'name': str(name.text),
                        'calorie': 0,
                        'time': meal
                    })

        driver.quit()
