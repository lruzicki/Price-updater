import mysql.connector
import requests
from select import select
import pandas as pd
import openpyxl
import logging
import schedule
import time

#Creating and Configuring Logger
Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(filename = "logfile.log",
                    filemode = "a",
                    format = Log_Format, 
                    level = logging.ERROR)

logger = logging.getLogger()

#Testing our Logger

mydb = mysql.connector.connect(host = "localhost", user = "root", passwd = "root")

#get all product and put them in var
mycursor = mydb.cursor()

mycursor.execute("select * FROM `mydb`.`Product`")

result = mycursor.fetchall()

# add coulumns to database
try:
    mycursor.execute("ALTER TABLE `mydb`.`Product` ADD `UnitPriceUSD` DECIMAL")
except:
    print("UnitPriceUSD already exists")
try:
    mycursor.execute("ALTER TABLE `mydb`.`Product` ADD `UnitPriceEURO` DECIMAL")
except:
    print("UnitPriceEURO already exists")
response = requests.get("http://api.nbp.pl/api/exchangerates/tables/a/")
if response.status_code != 200:
    logger.error("NBP API dosen't respond! Prices not updated!")


# take data from json file
exchange_info = response.json()
for i in exchange_info[0]['rates']:
    if i['code'] == 'EUR':
        current_euro_exchange = i['mid']
    if i['code'] == 'USD':
        current_usd_exchange = i['mid']  

# add foreign currency prices to mydb
all_products = mycursor.fetchall()
for iterate_product in result:
    foreign_currency_prices = (float(iterate_product[6]) / current_euro_exchange, float(iterate_product[6]) / current_usd_exchange, iterate_product[0])
    mycursor.execute("UPDATE `mydb`.`Product` SET `UnitPriceEURO` = %s, `UnitPriceUSD` = %s WHERE `ProductID` = %s", foreign_currency_prices)

mydb.commit()

# prepare data to import mydb to dataframe and excel file
mycursor.execute("SHOW COLUMNS FROM `mydb`.`Product`;")
result = mycursor.fetchall()
column_names = []
column_index = []
# set column order to match the client require order
for i in range(11):
    column_index.append(i)
    if i == 6:
        column_index += ([12, 13])
for i in column_index:
    column_names.append(result[i][0])

# make empty dataframe with coulmn names from mydb
df = pd.DataFrame(columns = column_names)

product_data = []
mycursor.execute("select * FROM `mydb`.`Product`")
result = mycursor.fetchall()

# make dict with pairs column name: value in client order
for product in result:
    dict = {column_names[i]: product[column_index[i]] for i in range(len(column_index))}
    df = df.append(dict, ignore_index = True)

# import dataframe to excel file
df.to_excel("products2.xlsx")

logger.error("UnitPriceEURO and UnitPriceUSD updated")